package cmd

import (
	"fmt"

	"github.com/pkg/errors"
	"github.com/spf13/cobra"

	"github.com/vmware-tanzu-labs/educates-training-platform/client-programs/pkg/cluster"
	"github.com/vmware-tanzu-labs/educates-training-platform/client-programs/pkg/config"
	"github.com/vmware-tanzu-labs/educates-training-platform/client-programs/pkg/installer"
)

func (o *PlatformDeployOptions) RunDelete() error {
	fullConfig, err := config.NewInstallationConfigFromFile(o.Config)

	if err != nil {
		return err
	}

	// This can be set in the config file if not provided via the command line
	if o.Provider != "" {
		fullConfig.ClusterInfrastructure.Provider = o.Provider
	}

	// Although ytt does some schema validation, we do some basic validation here
	if err := validateProvider(fullConfig.ClusterInfrastructure.Provider); err != nil {
		return err
	}

	installer := installer.NewInstaller()

	clusterConfig := cluster.NewClusterConfig(o.Kubeconfig, o.Context)

	err = installer.Delete(fullConfig, clusterConfig, o.Verbose)

	if err != nil {
		return errors.Wrap(err, "educates could not be deleted")
	}

	fmt.Println("\nEducates has been deleted succesfully")

	return nil
}

func (p *ProjectInfo) NewAdminPlatformDeleteCmd() *cobra.Command {
	var o PlatformDeployOptions

	var c = &cobra.Command{
		Args:  cobra.NoArgs,
		Use:   "delete",
		Short: "Delete Educates and related cluster services from your cluster",
		RunE: func(cmd *cobra.Command, _ []string) error {
			return o.RunDelete()
		},
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
		&o.Context,
		"context",
		"",
		"Context to use from Kubeconfig",
	)
	c.Flags().StringVar(
		&o.Provider,
		"provider",
		"",
		"infastructure provider deployment is being made to (eks, gke, kind, custom, vcluster)",
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
		"version to be installed",
	)

	c.MarkFlagRequired("config")

	return c
}
