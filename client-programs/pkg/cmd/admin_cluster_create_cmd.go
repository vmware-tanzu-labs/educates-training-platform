package cmd

import (
	"context"
	_ "embed"
	"fmt"
	"io"
	"os"

	"github.com/docker/docker/api/types"
	"github.com/docker/docker/api/types/container"
	"github.com/docker/docker/client"
	"github.com/docker/go-connections/nat"
	"github.com/pkg/errors"
	"github.com/spf13/cobra"
	"gopkg.in/yaml.v2"
	apiv1 "k8s.io/api/core/v1"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/client-go/kubernetes"

	"github.com/vmware-tanzu-labs/educates-training-platform/client-programs/pkg/cluster"
	"github.com/vmware-tanzu-labs/educates-training-platform/client-programs/pkg/config"
	"github.com/vmware-tanzu-labs/educates-training-platform/client-programs/pkg/installer"
	"github.com/vmware-tanzu-labs/educates-training-platform/client-programs/pkg/registry"
)

type AdminClusterCreateOptions struct {
	Config            string
	Kubeconfig        string
	ClusterImage      string
	Domain            string
	PackageRepository string
	Version           string
	ClusterOnly       bool
	Verbose           bool
}

func (o *AdminClusterCreateOptions) Run() error {
	fullConfig, err := config.NewInstallationConfigFromFile(o.Config)

	if err != nil {
		return err
	}

	if fullConfig.ClusterInfrastructure.Provider != "" && fullConfig.ClusterInfrastructure.Provider != "kind" {
		return errors.New("Only kind provider is supported for local cluster creation")
	}
	fullConfig.ClusterInfrastructure.Provider = "kind"

	// Since the installer will provide the default values for the given config, we don't really need to set them here
	// TODO: See what's a better way to customize this values when using local installer
	if !o.ClusterOnly {
		if o.Domain != "" {
			fullConfig.ClusterIngress.Domain = o.Domain

			// TODO: Why are we clearing the TLS certificate?
			fullConfig.ClusterIngress.TLSCertificate = config.TLSCertificateConfig{}

			// TODO: Why are we clearing the TLS certificateRef?
			fullConfig.ClusterIngress.TLSCertificateRef.Namespace = ""
			fullConfig.ClusterIngress.TLSCertificateRef.Name = ""

			// TODO: Why we don't clear the CA certificate and CertificateRef?
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
	}

	if o.Verbose {
		configData, err := yaml.Marshal(&fullConfig)
		if err != nil {
			return errors.Wrap(err, "failed to generate installation config")
		}
		fmt.Println("Configuration to be applied:")
		fmt.Println("-------------------------------")
		fmt.Println(string(configData))
		fmt.Println("###############################")
	}

	clusterConfig := cluster.NewKindClusterConfig(o.Kubeconfig)

	if exists, err := clusterConfig.ClusterExists(); exists && err != nil {
		return err
	}

	httpAvailable, err := checkPortAvailability(fullConfig.LocalKindCluster.ListenAddress, []uint{80, 443}, o.Verbose)

	if err != nil {
		return errors.Wrap(err, "couldn't test whether ports 80/443 available")
	}

	if !httpAvailable {
		return errors.New("ports 80/443 not available")
	}

	err = clusterConfig.CreateCluster(fullConfig, o.ClusterImage)

	if err != nil {
		return err
	}

	client, err := clusterConfig.Config.GetClient()

	if err != nil {
		return err
	}

	if !o.ClusterOnly {
		// This creates the educates-secrets namespace if it doesn't exist and creates the
		// wildcard and CA secrets in there
		if err = SyncSecretsToCluster(client); err != nil {
			return err
		}
	}

	if err = registry.DeployRegistry(); err != nil {
		return errors.Wrap(err, "failed to deploy registry")
	}

	if err = registry.LinkRegistryToCluster(); err != nil {
		return errors.Wrap(err, "failed to link registry to cluster")
	}

	// TODO: Remove this and function
	// if err = registry.UpdateRegistryService(client); err != nil {
	// 	return errors.Wrap(err, "failed to create service for registry")
	// }

	// TODO: Remove this and function
	// if err = createLoopbackService(client, fullConfig.ClusterIngress.Domain); err != nil {
	// 	return err
	// }

	if err = registry.AddRegistryConfigToKindNodes(); err != nil {
		return errors.Wrap(err, "failed to add registry config to kind nodes")
	}

	if err = registry.DocumentLocalRegistry(client); err != nil {
		return errors.Wrap(err, "failed to document registry config in cluster")
	}

	if !o.ClusterOnly {
		installer := installer.NewInstaller()
		err = installer.Run(o.Version, o.PackageRepository, fullConfig, &clusterConfig.Config, false, o.Verbose, false)
		if err != nil {
			return errors.Wrap(err, "educates could not be installed")
		}
	}

	fmt.Println("Educates cluster has been created succesfully")

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
		&o.PackageRepository,
		"package-repository",
		p.ImageRepository,
		"image repository hosting package bundles",
	)
	c.Flags().StringVar(
		&o.Version,
		"version",
		p.Version,
		"version of Educates training platform to be installed",
	)
	c.Flags().BoolVar(
		&o.ClusterOnly,
		"cluster-only",
		false,
		"only create the cluster, do not install Educates",
	)
	c.Flags().BoolVar(
		&o.Verbose,
		"verbose",
		false,
		"print verbose output",
	)
	return c
}

func checkPortAvailability(listenAddress string, ports []uint, verbose bool) (bool, error) {
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
	if verbose {
		io.Copy(os.Stdout, reader)
	}

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
