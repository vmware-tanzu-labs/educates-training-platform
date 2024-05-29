package cmd

import (
	"fmt"

	"github.com/pkg/errors"
	"github.com/spf13/cobra"

	"github.com/vmware-tanzu-labs/educates-training-platform/client-programs/pkg/cluster"
	"github.com/vmware-tanzu-labs/educates-training-platform/client-programs/pkg/registry"
)

type AdminRegistryDeployOptions struct {
	KubeconfigOptions
}

func (o *AdminRegistryDeployOptions) Run() error {
	err := registry.DeployRegistry()

	if err != nil {
		return errors.Wrap(err, "failed to deploy registry")
	}

	// This will fail if you do not have a Kubernetes cluster, but we can still
	// deploy just the image registry alone without Kubernetes. If a Kubernetes
	// cluster is created later, then the registry service will be added then.

	err = registry.LinkRegistryToCluster()

	if err != nil {
		fmt.Println("Warning: Kubernetes cluster not linked to image registry.")
	}

	clusterConfig := cluster.NewClusterConfig(o.Kubeconfig, o.Context)

	client, err := clusterConfig.GetClient()

	if err != nil {
		fmt.Println("Warning: Kubernetes cluster not updated with registry service.")

		return nil
	}

	if err = registry.UpdateRegistryService(client); err != nil {
		return errors.Wrap(err, "failed to create service for registry")
	}

	return nil
}

func (p *ProjectInfo) NewAdminRegistryDeployCmd() *cobra.Command {
	var o AdminRegistryDeployOptions

	var c = &cobra.Command{
		Args:  cobra.NoArgs,
		Use:   "deploy",
		Short: "Deploys a local image registry",
		RunE:  func(_ *cobra.Command, _ []string) error { return o.Run() },
	}

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

	return c
}
