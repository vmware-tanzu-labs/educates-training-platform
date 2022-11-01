// Copyright 2022 The Educates Authors.

package cmd

import (
	"github.com/spf13/cobra"
)

func (p *ProjectInfo) NewConfigCmdGroup() *cobra.Command {
	var c = &cobra.Command{
		Use:   "package-config",
		Short: "Manage configuration files",
	}

	c.AddCommand(
		p.NewConfigEditCmd(),
		p.NewConfigViewCmd(),
		p.NewConfigResetCmd(),
	)

	return c
}
