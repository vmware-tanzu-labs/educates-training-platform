// Copyright 2022 The Educates Authors.

package cmd

import (
	"github.com/spf13/cobra"
)

func (p *ProjectInfo) NewOperatorsCmdGroup() *cobra.Command {
	var c = &cobra.Command{
		Use:   "training-platform",
		Short: "Install platform operators",
	}

	c.AddCommand(
		p.NewOperatorsDeployCmd(),
		NewOperatorsDeleteCmd(),
	)

	return c
}
