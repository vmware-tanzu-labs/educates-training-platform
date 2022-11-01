// Copyright 2022 The Educates Authors.

package cmd

import (
	"github.com/spf13/cobra"

	"github.com/vmware-tanzu-labs/educates-training-platform/client-programs/pkg/cluster"
	"github.com/vmware-tanzu-labs/educates-training-platform/client-programs/pkg/config"
	"github.com/vmware-tanzu-labs/educates-training-platform/client-programs/pkg/services"
)

type AdminServicesDeleteOptions struct {
	Config     string
	Kubeconfig string
}

func (o *AdminServicesDeleteOptions) Run() error {
	fullConfig, err := config.NewInstallationConfigFromFile(o.Config)

	if err != nil {
		return err
	}

	clusterConfig := cluster.NewClusterConfig(o.Kubeconfig)

	servicesConfig := config.ClusterEssentialsConfig{
		ClusterInfrastructure: fullConfig.ClusterInfrastructure,
		ClusterPackages:       fullConfig.ClusterPackages,
		ClusterSecurity:       fullConfig.ClusterSecurity,
	}

	return services.DeleteServices(clusterConfig, &servicesConfig)
}

func (p *ProjectInfo) NewAdminServicesDeleteCmd() *cobra.Command {
	var o AdminServicesDeleteOptions

	var c = &cobra.Command{
		Args:  cobra.NoArgs,
		Use:   "delete",
		Short: "Delete cluster services",
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
		"kubeconfig file to use instead of $KUBECONFIG or $HOME/.kube/config",
	)

	return c
}
