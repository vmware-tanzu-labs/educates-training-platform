/*
Copyright © 2022 The Educates Authors.
*/
package cmd

import (
	"github.com/spf13/cobra"

	"github.com/vmware-tanzu-labs/educates-training-platform/client-programs/pkg/cluster"
	"github.com/vmware-tanzu-labs/educates-training-platform/client-programs/pkg/registry"
	"github.com/vmware-tanzu-labs/educates-training-platform/client-programs/pkg/resolver"
)

type ClusterDeleteOptions struct {
	Kubeconfig    string
	AllComponents bool
}

func (o *ClusterDeleteOptions) Run() error {
	c := cluster.NewKindClusterConfig(o.Kubeconfig)

	if o.AllComponents {
		registry.DeleteRegistry()
		resolver.DeleteResolver()
	}

	return c.DeleteCluster()
}

func NewClusterDeleteCmd() *cobra.Command {
	var o ClusterDeleteOptions

	var c = &cobra.Command{
		Args:  cobra.NoArgs,
		Use:   "delete",
		Short: "Deletes the local Kind cluster",
		RunE:  func(_ *cobra.Command, _ []string) error { return o.Run() },
	}

	c.Flags().StringVar(
		&o.Kubeconfig,
		"kubeconfig",
		"",
		"kubeconfig file to use instead of $KUBECONFIG or $HOME/.kube/config",
	)
	c.Flags().BoolVar(
		&o.AllComponents,
		"all",
		false,
		"delete everything, including image registry and resolver",
	)

	return c
}
