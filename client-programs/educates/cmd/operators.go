/*
Copyright © 2022 The Educates Authors.
*/
package cmd

import (
	"github.com/spf13/cobra"
)

func NewOperatorsCmd() *cobra.Command {
	var operatorsCmd = &cobra.Command{
		Use:   "training-platform",
		Short: "Manage platform operators",
	}

	operatorsCmd.AddCommand(
		NewOperatorsDeleteCmd(),
		NewOperatorsDeployCmd(),
	)

	return operatorsCmd
}
