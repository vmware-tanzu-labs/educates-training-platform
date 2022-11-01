// Copyright 2022 The Educates Authors.

package cmd

import (
	"github.com/pkg/errors"
	"github.com/spf13/cobra"
	"github.com/vmware-tanzu-labs/educates-training-platform/client-programs/pkg/cluster"
)

type SecretsSyncOptions struct {
	Kubeconfig string
}

func (o *SecretsSyncOptions) Run() error {
	clusterConfig := cluster.NewKindClusterConfig(o.Kubeconfig)

	client, err := clusterConfig.GetClient()

	if err != nil {
		return errors.Wrapf(err, "unable to create Kubernetes client")
	}

	return SyncSecretsToCluster(client)
}

func (p *ProjectInfo) NewSecretsSyncCmd() *cobra.Command {
	var o SecretsSyncOptions

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
