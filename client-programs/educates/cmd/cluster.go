/*
Copyright © 2022 The Educates Authors.
*/
package cmd

import (
	"github.com/spf13/cobra"
)

func NewClusterCmd() *cobra.Command {
	var configCmd = &cobra.Command{
		Use:   "cluster",
		Short: "Manage local Kind cluster",
	}

	configCmd.AddCommand(
		NewClusterCreateCmd(),
		NewClusterDeleteCmd(),
	)

	return configCmd
}
