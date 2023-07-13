// Copyright 2022-2023 The Educates Authors.

package cmd

import (
	"context"
	_ "embed"
	"fmt"
	"io"
	"os"
	"time"

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

	"github.com/vmware-tanzu-labs/educates-training-platform/client-programs/pkg/cluster"
	"github.com/vmware-tanzu-labs/educates-training-platform/client-programs/pkg/config"
	"github.com/vmware-tanzu-labs/educates-training-platform/client-programs/pkg/operators"
	"github.com/vmware-tanzu-labs/educates-training-platform/client-programs/pkg/registry"
	"github.com/vmware-tanzu-labs/educates-training-platform/client-programs/pkg/services"
)

type AdminClusterCreateOptions struct {
	Config     string
	Kubeconfig string
	Image      string
	Domain     string
	Version    string
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

	kappConfig.FileFlags = tools.FileFlags{
		Files: []string{
			"https://github.com/vmware-tanzu/carvel-kapp-controller/releases/latest/download/release.yml",
		},
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

	servicesConfig := config.ClusterEssentialsConfig{
		ClusterInfrastructure: fullConfig.ClusterInfrastructure,
		ClusterPackages:       fullConfig.ClusterPackages,
		ClusterSecurity:       fullConfig.ClusterSecurity,
	}

	if err = services.DeployServices(o.Version, &clusterConfig.ClusterConfig, &servicesConfig); err != nil {
		return errors.Wrap(err, "failed to deploy services")
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
		return errors.Wrap(err, "failed to deploy operators")
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
		&o.Image,
		"image",
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
