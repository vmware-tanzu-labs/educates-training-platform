/*
Copyright © 2022 The Educates Authors.
*/
package cmd

import (
	"github.com/pkg/errors"
	"github.com/spf13/cobra"

	"github.com/vmware-tanzu-labs/educates-training-platform/client-programs/educates/pkg/cluster"
	"github.com/vmware-tanzu-labs/educates-training-platform/client-programs/educates/pkg/registry"
)

type RegistryDeployOptions struct {
	Kubeconfig string
}

func (o *RegistryDeployOptions) Run() error {
	clusterConfig := cluster.NewKindClusterConfig(o.Kubeconfig)

	client, err := clusterConfig.GetClient()

	if err != nil {
		return err
	}

	err = registry.DeployRegistry()

	if err != nil {
		return errors.Wrap(err, "failed to deploy registry")
	}

	// XXX This will fail if do not have a Kubernetes cluster, but we should
	// be able to deploy just the image registry alone without Kubernetes.

	if err = registry.UpdateRegistryService(client); err != nil {
		return errors.Wrap(err, "failed to create service for registry")
	}

	return nil
}

func NewRegistryDeployCmd() *cobra.Command {
	var o RegistryDeployOptions

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

	return c
}
