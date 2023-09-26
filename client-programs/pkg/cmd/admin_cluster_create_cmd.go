package cmd

import (
	"context"
	_ "embed"
	"fmt"
	"io"
	"os"
	"path"
	"time"

	"github.com/adrg/xdg"
	"github.com/cppforlife/go-cli-ui/ui"
	"github.com/docker/docker/api/types"
	"github.com/docker/docker/api/types/container"
	"github.com/docker/docker/client"
	"github.com/docker/go-connections/nat"
	"github.com/pkg/errors"
	"github.com/spf13/cobra"
	"github.com/vmware-tanzu/carvel-kapp/pkg/kapp/cmd"
	"github.com/vmware-tanzu/carvel-kapp/pkg/kapp/cmd/app"
	"github.com/vmware-tanzu/carvel-kapp/pkg/kapp/cmd/core"
	"github.com/vmware-tanzu/carvel-kapp/pkg/kapp/cmd/tools"
	"github.com/vmware-tanzu/carvel-kapp/pkg/kapp/logger"
	"gopkg.in/yaml.v2"
	apiv1 "k8s.io/api/core/v1"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/runtime"
	"k8s.io/client-go/kubernetes"
	"k8s.io/kubectl/pkg/scheme"

	"github.com/vmware-tanzu-labs/educates-training-platform/client-programs/pkg/cluster"
	"github.com/vmware-tanzu-labs/educates-training-platform/client-programs/pkg/config"
	"github.com/vmware-tanzu-labs/educates-training-platform/client-programs/pkg/operators"
	"github.com/vmware-tanzu-labs/educates-training-platform/client-programs/pkg/registry"
	"github.com/vmware-tanzu-labs/educates-training-platform/client-programs/pkg/services"
)

type AdminClusterCreateOptions struct {
	Config                string
	Kubeconfig            string
	Image                 string
	Domain                string
	Version               string
	KappControllerVersion string
	WithServices          bool
	WithPlatform          bool
}

func (o *AdminClusterCreateOptions) Run() error {
	fullConfig, err := config.NewInstallationConfigFromFile(o.Config)

	if err != nil {
		return err
	}

	fullConfig.ClusterInfrastructure.Provider = "kind"

	if o.Domain != "" {
		fullConfig.ClusterIngress.Domain = o.Domain

		fullConfig.ClusterIngress.TLSCertificate = config.TLSCertificateConfig{}

		fullConfig.ClusterIngress.TLSCertificateRef.Namespace = ""
		fullConfig.ClusterIngress.TLSCertificateRef.Name = ""
	}

	if secretName := CachedSecretForIngressDomain(fullConfig.ClusterIngress.Domain); secretName != "" {
		fullConfig.ClusterIngress.TLSCertificateRef.Namespace = "educates-secrets"
		fullConfig.ClusterIngress.TLSCertificateRef.Name = secretName
	}

	if secretName := CachedSecretForCertificateAuthority(fullConfig.ClusterIngress.Domain); secretName != "" {
		fullConfig.ClusterIngress.CACertificateRef.Namespace = "educates-secrets"
		fullConfig.ClusterIngress.CACertificateRef.Name = secretName
	}

	if fullConfig.ClusterIngress.CACertificateRef.Name != "" || fullConfig.ClusterIngress.CACertificate.Certificate != "" {
		fullConfig.ClusterIngress.CANodeInjector.Enabled = true
	}

	clusterConfig := cluster.NewKindClusterConfig(o.Kubeconfig)

	httpAvailable, err := checkPortAvailability(fullConfig.LocalKindCluster.ListenAddress, []uint{80, 443})

	if err != nil {
		return errors.Wrap(err, "couldn't test whether ports 80/443 available")
	}

	if !httpAvailable {
		return errors.New("ports 80/443 not available")
	}

	err = clusterConfig.CreateCluster(fullConfig, o.Image)

	if err != nil {
		return err
	}

	client, err := clusterConfig.GetClient()

	if err != nil {
		return err
	}

	err = SyncSecretsToCluster(client)

	if err != nil {
		return err
	}

	confUI := ui.NewConfUI(ui.NewNoopLogger())

	uiFlags := cmd.UIFlags{
		Color:          true,
		JSON:           false,
		NonInteractive: true,
	}

	uiFlags.ConfigureUI(confUI)

	defer confUI.Flush()

	configFactory := core.NewConfigFactoryImpl()
	configFactory.ConfigurePathResolver(func() (string, error) { return clusterConfig.Kubeconfig, nil })
	configFactory.ConfigureContextResolver(func() (string, error) { return "", nil })
	configFactory.ConfigureYAMLResolver(func() (string, error) { return "", nil })

	depsFactory := core.NewDepsFactoryImpl(configFactory, confUI)
	kappLogger := logger.NewUILogger(confUI)

	kappConfig := app.NewDeployOptions(confUI, depsFactory, kappLogger)

	kappConfig.AppFlags = app.Flags{
		Name: "kapp-controller",
		NamespaceFlags: core.NamespaceFlags{
			Name: "default",
		},
	}

	var deploymentFiles []string

	if fullConfig.ClusterIngress.CACertificateRef.Name != "" {
		configFileDir := path.Join(xdg.DataHome, "educates")
		secretsCacheDir := path.Join(configFileDir, "secrets")
		name := fullConfig.ClusterIngress.CACertificateRef.Name + ".yaml"
		certificateFullPath := path.Join(secretsCacheDir, name)

		secretYAML, err := os.ReadFile(certificateFullPath)

		if err != nil {
			return errors.Wrap(err, "unable to read CA certificate secret file")
		}

		parsedSecret := &apiv1.Secret{}
		decoder := scheme.Codecs.UniversalDeserializer()

		_, _, err = decoder.Decode([]byte(secretYAML), nil, parsedSecret)

		if err != nil {
			return errors.Wrap(err, "unable to parse CA certificate secret file")
		}

		certificateData, found := parsedSecret.Data["ca.crt"]

		if !found {
			return errors.New("CA certificate secret file doesn't contain ca.crt")
		}

		kappConfigSecret := &apiv1.Secret{
			TypeMeta: metav1.TypeMeta{
				APIVersion: "v1",
				Kind:       "Secret",
			},
			ObjectMeta: metav1.ObjectMeta{
				Name:      "kapp-controller-config",
				Namespace: "kapp-controller",
			},
			StringData: map[string]string{
				"caCerts": string(certificateData),
			},
		}

		kappConfigObject, err := runtime.DefaultUnstructuredConverter.ToUnstructured(kappConfigSecret)

		if err != nil {
			return errors.Wrap(err, "cannot convert kapp-controller config to object")
		}

		kappConfigYAML, err := yaml.Marshal(&kappConfigObject)

		if err != nil {
			return errors.Wrap(err, "couldn't generate YAML for kapp-controller config")
		}

		kappConfigPath := path.Join(configFileDir, "kapp-controller-config.yaml")

		err = os.WriteFile(kappConfigPath, kappConfigYAML, 0644)

		if err != nil {
			return errors.Wrap(err, "cannot write kapp-controller config file")
		}

		deploymentFiles = append(deploymentFiles, kappConfigPath)
	}

	deploymentFiles = append(deploymentFiles, fmt.Sprintf("https://github.com/carvel-dev/kapp-controller/releases/download/v%s/release.yml", o.KappControllerVersion))

	kappConfig.FileFlags = tools.FileFlags{
		Files: deploymentFiles,
	}

	kappConfig.ApplyFlags.ClusterChangeOpts.Wait = true

	kappConfig.ApplyFlags.ApplyingChangesOpts.Concurrency = 5

	kappConfig.ApplyFlags.WaitingChangesOpts.CheckInterval = time.Duration(1) * time.Second
	kappConfig.ApplyFlags.WaitingChangesOpts.Timeout = time.Duration(15) * time.Minute
	kappConfig.ApplyFlags.WaitingChangesOpts.Concurrency = 5

	kappConfig.DeployFlags.ExistingNonLabeledResourcesCheck = false
	kappConfig.DeployFlags.ExistingNonLabeledResourcesCheckConcurrency = 5
	kappConfig.DeployFlags.AppChangesMaxToKeep = 5

	err = kappConfig.Run()

	if err != nil {
		return errors.Wrap(err, "failed to deploy kapp-controller")
	}

	err = registry.DeployRegistry()

	if err != nil {
		return errors.Wrap(err, "failed to deploy registry")
	}

	err = registry.LinkRegistryToCluster()

	if err != nil {
		return errors.Wrap(err, "failed to link registry to cluster")
	}

	if err = registry.UpdateRegistryService(client); err != nil {
		return errors.Wrap(err, "failed to create service for registry")
	}

	if err = createLoopbackService(client, fullConfig.ClusterIngress.Domain); err != nil {
		return err
	}

	if !o.WithServices {
		return nil
	}

	servicesConfig := config.ClusterEssentialsConfig{
		ClusterInfrastructure: fullConfig.ClusterInfrastructure,
		ClusterPackages:       fullConfig.ClusterPackages,
		ClusterSecurity:       fullConfig.ClusterSecurity,
	}

	if err = services.DeployServices(o.Version, &clusterConfig.ClusterConfig, &servicesConfig); err != nil {
		return errors.Wrap(err, "failed to deploy cluster essentials services")
	}

	if !o.WithPlatform {
		return nil
	}

	platformConfig := config.TrainingPlatformConfig{
		ClusterSecurity:   fullConfig.ClusterSecurity,
		ClusterRuntime:    fullConfig.ClusterRuntime,
		ClusterIngress:    fullConfig.ClusterIngress,
		SessionCookies:    fullConfig.SessionCookies,
		ClusterStorage:    fullConfig.ClusterStorage,
		ClusterSecrets:    fullConfig.ClusterSecrets,
		TrainingPortal:    fullConfig.TrainingPortal,
		WorkshopSecurity:  fullConfig.WorkshopSecurity,
		ImageRegistry:     fullConfig.ImageRegistry,
		ImageVersions:     fullConfig.ImageVersions,
		DockerDaemon:      fullConfig.DockerDaemon,
		ClusterNetwork:    fullConfig.ClusterNetwork,
		WorkshopAnalytics: fullConfig.WorkshopAnalytics,
		WebsiteStyling:    fullConfig.WebsiteStyling,
	}

	if err = operators.DeployOperators(o.Version, &clusterConfig.ClusterConfig, &platformConfig); err != nil {
		return errors.Wrap(err, "failed to deploy training platform components")
	}

	return nil
}

func (p *ProjectInfo) NewAdminClusterCreateCmd() *cobra.Command {
	var o AdminClusterCreateOptions

	var c = &cobra.Command{
		Args:  cobra.NoArgs,
		Use:   "create",
		Short: "Creates a local Kubernetes cluster",
		RunE:  func(_ *cobra.Command, _ []string) error { return o.Run() },
	}

	c.Flags().StringVar(
		&o.Config,
		"config",
		"",
		"path to the installation config file for Educates",
	)
	c.Flags().StringVar(
		&o.Kubeconfig,
		"kubeconfig",
		"",
		"kubeconfig file to use instead of $HOME/.kube/config",
	)
	c.Flags().StringVar(
		&o.ClusterImage,
		"kind-cluster-image",
		"",
		"docker image to use when booting the kind cluster",
	)
	c.Flags().StringVar(
		&o.Domain,
		"domain",
		"",
		"wildcard ingress subdomain name for Educates",
	)
	c.Flags().StringVar(
		&o.Version,
		"version",
		p.Version,
		"version of Educates training platform to be installed",
	)
	c.Flags().StringVar(
		&o.KappControllerVersion,
		"kapp-controller-version",
		"0.47.0",
		"version of kapp-controller operator to be installed",
	)
	c.Flags().BoolVar(
		&o.WithServices,
		"with-services",
		true,
		"deploy extra cluster services required for Educates",
	)
	c.Flags().BoolVar(
		&o.WithPlatform,
		"with-platform",
		true,
		"deploy all the Educates training platform components",
	)

	return c
}

func checkPortAvailability(listenAddress string, ports []uint) (bool, error) {
	ctx := context.Background()

	cli, err := client.NewClientWithOpts(client.FromEnv)

	if err != nil {
		return false, errors.Wrap(err, "unable to create docker client")
	}

	cli.ContainerRemove(ctx, "educates-port-availability-check", types.ContainerRemoveOptions{})

	reader, err := cli.ImagePull(ctx, "docker.io/library/busybox:latest", types.ImagePullOptions{})
	if err != nil {
		return false, errors.Wrap(err, "cannot pull busybox image")
	}

	defer reader.Close()
	io.Copy(os.Stdout, reader)

	if listenAddress == "" {
		listenAddress, err = config.HostIP()

		if err != nil {
			listenAddress = "127.0.0.1"
		}
	}

	hostConfig := &container.HostConfig{
		PortBindings: nat.PortMap{},
	}

	exposedPorts := nat.PortSet{}

	for _, port := range ports {
		key := nat.Port(fmt.Sprintf("%d/tcp", port))
		hostConfig.PortBindings[key] = []nat.PortBinding{
			{
				HostIP:   listenAddress,
				HostPort: fmt.Sprintf("%d", port),
			},
		}
		exposedPorts[key] = struct{}{}
	}

	resp, err := cli.ContainerCreate(ctx, &container.Config{
		Image:        "docker.io/library/busybox:latest",
		Cmd:          []string{"/bin/true"},
		Tty:          false,
		ExposedPorts: exposedPorts,
	}, hostConfig, nil, nil, "educates-port-availability-check")

	if err != nil {
		return false, errors.Wrap(err, "cannot create busybox container")
	}

	defer cli.ContainerRemove(ctx, "educates-port-availability-check", types.ContainerRemoveOptions{})

	if err := cli.ContainerStart(ctx, resp.ID, types.ContainerStartOptions{}); err != nil {
		return false, errors.Wrap(err, "cannot start busybox container")
	}

	statusCh, errCh := cli.ContainerWait(ctx, "educates-port-availability-check", container.WaitConditionNotRunning)

	select {
	case err := <-errCh:
		if err != nil {
			return false, nil
		}
	case <-statusCh:
	}

	return true, nil
}

func createLoopbackService(k8sclient *kubernetes.Clientset, domain string) error {
	service := apiv1.Service{
		ObjectMeta: metav1.ObjectMeta{
			Name: "loopback",
		},
		Spec: apiv1.ServiceSpec{
			Type:         apiv1.ServiceTypeExternalName,
			ExternalName: fmt.Sprintf("localhost.%s", domain),
		},
	}

	servicesClient := k8sclient.CoreV1().Services("default")

	servicesClient.Delete(context.TODO(), "loopback", *metav1.NewDeleteOptions(0))

	_, err := servicesClient.Create(context.TODO(), &service, metav1.CreateOptions{})

	if err != nil {
		return errors.Wrap(err, "unable to create localhost loopback service")
	}

	return nil
}
