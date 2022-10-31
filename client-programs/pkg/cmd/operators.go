// Copyright 2022 The Educates Authors.

package cmd

import (
	"github.com/spf13/cobra"
)

func (info *ProjectInfo) NewOperatorsCmd() *cobra.Command {
	var operatorsCmd = &cobra.Command{
		Use:   "training-platform",
		Short: "Install platform operators",
	}

	operatorsCmd.AddCommand(
		info.NewOperatorsDeployCmd(),
		NewOperatorsDeleteCmd(),
	)

	return operatorsCmd
}
