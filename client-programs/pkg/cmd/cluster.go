// Copyright 2022 The Educates Authors.

package cmd

import (
	"github.com/spf13/cobra"
)

func (info *ProjectInfo) NewClusterCmd() *cobra.Command {
	var configCmd = &cobra.Command{
		Use:   "kind-cluster",
		Short: "Manage local Kubernetes cluster",
	}

	configCmd.AddCommand(
		info.NewClusterCreateCmd(),
		NewClusterStartCmd(),
		NewClusterStopCmd(),
		NewClusterDeleteCmd(),
	)

	return configCmd
}
