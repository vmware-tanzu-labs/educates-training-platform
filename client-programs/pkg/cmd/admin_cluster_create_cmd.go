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

	"github.com/vmware-tanzu-labs/educates-training-platform/client-programs/pkg/cluster"
	"github.com/vmware-tanzu-labs/educates-training-platform/client-programs/pkg/config"
	"github.com/vmware-tanzu-labs/educates-training-platform/client-programs/pkg/installer"
	"github.com/vmware-tanzu-labs/educates-training-platform/client-programs/pkg/registry"
	"github.com/vmware-tanzu-labs/educates-training-platform/client-programs/pkg/secrets"
	"github.com/vmware-tanzu-labs/educates-training-platform/client-programs/pkg/utils"
)

var (
	createExample = `
	# Create local educates cluster (no configuration, uses nip.io wildcard domain and Kind as provider config defaults)
	educates admin cluster create

	# Create local educates cluster with custom configuration
	educates admin cluster create --config config.yaml

	# Create local kind cluster but don't install anything on it (it creates local registry but not local secrets)
	educates admin cluster create --cluster-only

	# Create local kind cluster but don't install anything on it, but providing some config for kind
	educates admin cluster create --cluster-only --config config.yaml

	# Create local educates cluster and sync local educates secrets
	educates admin cluster create --config config.yaml --with-local-secrets

	# Create local educates cluster with bundle from different repository
	educates admin cluster create --package-repository ghcr.io/jorgemoralespou --version installer-clean

	# Create local educates cluster with local build (for development)
	educates admin cluster create --package-repository localhost:5001 --version 0.0.1
`
)

type AdminClusterCreateOptions struct {
	Config              string
	Kubeconfig          string
	ClusterImage        string
	Domain              string
	PackageRepository   string
	Version             string
	ClusterOnly         bool
	Verbose             bool
	WithLocalSecrets    bool
	skipImageResolution bool
}

func (o *AdminClusterCreateOptions) Run() error {
	var fullConfig *config.InstallationConfig
	var err error = nil

	if o.Config == "" {
		fullConfig, err = config.NewDefaultInstallationConfig()
	} else {
		fullConfig, err = config.NewInstallationConfigFromFile(o.Config)
	}

	if err != nil {
		return err
	}

	if fullConfig.ClusterInfrastructure.Provider != "" &&
		fullConfig.ClusterInfrastructure.Provider != "kind" &&
		fullConfig.ClusterInfrastructure.Provider != "custom" {
		return errors.New("Only kind or custom providers are supported for local cluster creation. If not provided, will default to kind")
	}
	if fullConfig.ClusterInfrastructure.Provider == "" {
		fullConfig.ClusterInfrastructure.Provider = "kind"
	}

	// We do resolve domain configuration precedence here
	fullConfig.ClusterIngress.Domain = config.EducatesDomain(fullConfig)

	// Since the installer will provide the default values for the given config, we don't really need to set them here
	// TODO: See what's a better way to customize this values when using local installer
	if !o.ClusterOnly && o.WithLocalSecrets {
		if fullConfig.ClusterInfrastructure.Provider != "kind" {
			return errors.New("Local secrets are only supported for kind clusters provider")
		}

		if o.Domain != "" {
			fullConfig.ClusterIngress.Domain = o.Domain

			// // TODO: Why are we clearing the TLS certificate?
			// fullConfig.ClusterIngress.TLSCertificate = config.TLSCertificateConfig{}

			// // TODO: Why are we clearing the TLS certificateRef?
			// fullConfig.ClusterIngress.TLSCertificateRef.Namespace = ""
			// fullConfig.ClusterIngress.TLSCertificateRef.Name = ""

			// // TODO: Why we don't clear the CA certificate and CertificateRef?
		}

		if secretName := secrets.LocalCachedSecretForIngressDomain(fullConfig.ClusterIngress.Domain); secretName != "" {
			fullConfig.ClusterIngress.TLSCertificateRef.Namespace = "educates-secrets"
			fullConfig.ClusterIngress.TLSCertificateRef.Name = secretName
		}

		if secretName := secrets.LocalCachedSecretForCertificateAuthority(fullConfig.ClusterIngress.Domain); secretName != "" {
			fullConfig.ClusterIngress.CACertificateRef.Namespace = "educates-secrets"
			fullConfig.ClusterIngress.CACertificateRef.Name = secretName
		}

		if fullConfig.ClusterIngress.CACertificateRef.Name != "" || fullConfig.ClusterIngress.CACertificate.Certificate != "" {
			fullConfig.ClusterIngress.CANodeInjector.Enabled = utils.BoolPointer(true)
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

	// This creates the educates-secrets namespace if it doesn't exist and creates the
	// wildcard and CA secrets in there
	if !o.ClusterOnly && o.WithLocalSecrets {
		if err = secrets.SyncLocalCachedSecretsToCluster(client); err != nil {
			return err
		}
	}

	if err = registry.DeployRegistry(); err != nil {
		return errors.Wrap(err, "failed to deploy registry")
	}

	if err = registry.LinkRegistryToCluster(); err != nil {
		return errors.Wrap(err, "failed to link registry to cluster")
	}

	// This is needed for imgpkg pull from locally published workshops
	if err = registry.UpdateRegistryService(client); err != nil {
		return errors.Wrap(err, "failed to create service for registry")
	}

	// This is for hugo livereload (educates serve-workshop)
	if err = cluster.CreateLoopbackService(client, fullConfig.ClusterIngress.Domain); err != nil {
		return err
	}

	// This is needed to make containerd use the local registry
	if err = registry.AddRegistryConfigToKindNodes("localhost:5001"); err != nil {
		return errors.Wrap(err, "failed to add registry config to kind nodes")
	}
	if err = registry.AddRegistryConfigToKindNodes("registry.default.svc.cluster.local"); err != nil {
		return errors.Wrap(err, "failed to add registry config to kind nodes")
	}

	// This is needed so that kubernetes nodes can pull images from the local registry
	if err = registry.DocumentLocalRegistry(client); err != nil {
		return errors.Wrap(err, "failed to document registry config in cluster")
	}

	if !o.ClusterOnly {
		installer := installer.NewInstaller()
		err = installer.Run(o.Version, o.PackageRepository, fullConfig, &clusterConfig.Config, o.Verbose, false, o.skipImageResolution, false)
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
		Args:    cobra.NoArgs,
		Use:     "create",
		Short:   "Creates a local Kubernetes cluster",
		RunE:    func(_ *cobra.Command, _ []string) error { return o.Run() },
		Example: createExample,
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
	c.Flags().BoolVar(
		&o.WithLocalSecrets,
		"with-local-secrets",
		false,
		"show the configuration augmented with local secrets if they exist for the given domain",
	)
	c.Flags().BoolVar(
		&o.skipImageResolution,
		"skip-image-resolution",
		false,
		"skips resolution of referenced images so that all will be fetched from their original location",
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
