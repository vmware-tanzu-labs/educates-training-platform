// Copyright 2022-2023 The Educates Authors.

package cmd

import (
	"github.com/pkg/errors"
	"github.com/spf13/cobra"
	"github.com/vmware-tanzu-labs/educates-training-platform/client-programs/pkg/cluster"
)

type AdminSecretsSyncOptions struct {
	Kubeconfig string
}

func (o *AdminSecretsSyncOptions) Run() error {
	clusterConfig := cluster.NewKindClusterConfig(o.Kubeconfig)

	client, err := clusterConfig.GetClient()

	if err != nil {
		return errors.Wrapf(err, "unable to create Kubernetes client")
	}

	return SyncSecretsToCluster(client)
}

func (p *ProjectInfo) NewAdminSecretsSyncCmd() *cobra.Command {
	var o AdminSecretsSyncOptions

	var c = &cobra.Command{
		Args:  cobra.NoArgs,
		Use:   "sync",
		Short: "Copy secrets to cluster",
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
