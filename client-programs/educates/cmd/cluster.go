/*
Copyright © 2022 The Educates Authors.
*/
package cmd

import (
	"github.com/spf13/cobra"
)

func NewClusterCmd() *cobra.Command {
	var configCmd = &cobra.Command{
		Use:   "local-cluster",
		Short: "Manage local Kubernetes cluster",
	}

	configCmd.AddCommand(
		NewClusterCreateCmd(),
		NewClusterDeleteCmd(),
		NewClusterStartCmd(),
		NewClusterStopCmd(),
	)

	return configCmd
}
