// Copyright 2022 The Educates Authors.

package cmd

import (
	"github.com/spf13/cobra"
)

func NewClusterCmd() *cobra.Command {
	var configCmd = &cobra.Command{
		Use:   "kind-cluster",
		Short: "Manage local Kubernetes cluster",
	}

	configCmd.AddCommand(
		NewClusterCreateCmd(),
		NewClusterStartCmd(),
		NewClusterStopCmd(),
		NewClusterDeleteCmd(),
	)

	return configCmd
}
