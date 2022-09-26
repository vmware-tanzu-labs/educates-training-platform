/*
Copyright © 2022 The Educates Authors.
*/
package cmd

import (
	"github.com/spf13/cobra"

	"github.com/vmware-tanzu-labs/educates-training-platform/client-programs/educates/pkg/cluster"
	"github.com/vmware-tanzu-labs/educates-training-platform/client-programs/educates/pkg/config"
	"github.com/vmware-tanzu-labs/educates-training-platform/client-programs/educates/pkg/services"
)

type ServicesDeployOptions struct {
	Config     string
	Kubeconfig string
	Version    string
}

func (o *ServicesDeployOptions) Run() error {
	fullConfig, err := config.NewInstallationConfigFromFile(o.Config)

	if err != nil {
		return err
	}

	fullConfig.ClusterInfrastructure.Provider = "kind"

	clusterConfig := cluster.NewClusterConfig(o.Kubeconfig)

	servicesConfig := config.ClusterEssentialsConfig{
		ClusterInfrastructure: fullConfig.ClusterInfrastructure,
		ClusterPackages:       fullConfig.ClusterPackages,
		ClusterSecurity:       fullConfig.ClusterSecurity,
	}

	return services.DeployServices(o.Version, clusterConfig, &servicesConfig)
}

func NewServicesDeployCmd() *cobra.Command {
	var o ServicesDeployOptions

	var c = &cobra.Command{
		Args:  cobra.NoArgs,
		Use:   "deploy",
		Short: "Deploy cluster services",
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
	c.Flags().StringVar(
		&o.Version,
		"version",
		"2.0.8",
		"version to be installed",
	)

	return c
}
