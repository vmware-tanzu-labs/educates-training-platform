/*
Copyright © 2022 The Educates Authors.
*/
package cmd

import (
	"github.com/spf13/cobra"
)

func NewConfigCmd() *cobra.Command {
	var configCmd = &cobra.Command{
		Use:   "package-config",
		Short: "Manage configuration files",
	}

	configCmd.AddCommand(
		NewConfigEditCmd(),
		NewConfigResetCmd(),
		NewConfigViewCmd(),
	)

	return configCmd
}
