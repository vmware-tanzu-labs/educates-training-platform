// Copyright 2022-2023 The Educates Authors.

package cmd

import (
	"github.com/spf13/cobra"

	"github.com/vmware-tanzu-labs/educates-training-platform/client-programs/pkg/cluster"
	"github.com/vmware-tanzu-labs/educates-training-platform/client-programs/pkg/config"
	"github.com/vmware-tanzu-labs/educates-training-platform/client-programs/pkg/operators"
)

type AdminPlatformDeleteOptions struct {
	Config     string
	Kubeconfig string
}

func (o *AdminPlatformDeleteOptions) Run() error {
	fullConfig, err := config.NewInstallationConfigFromFile(o.Config)

	if err != nil {
		return err
	}

	clusterConfig := cluster.NewClusterConfig(o.Kubeconfig)

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

	return operators.DeleteOperators(clusterConfig, &platformConfig)
}

func (p *ProjectInfo) NewAdminPlatformDeleteCmd() *cobra.Command {
	var o AdminPlatformDeleteOptions

	var c = &cobra.Command{
		Args:  cobra.NoArgs,
		Use:   "delete",
		Short: "Delete platform operators",
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
