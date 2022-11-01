// Copyright 2022 The Educates Authors.

package cmd

import (
	"github.com/spf13/cobra"
)

func (p *ProjectInfo) NewResolverCmdGroup() *cobra.Command {
	var c = &cobra.Command{
		Use:   "dns-resolver",
		Short: "Manage local DNS resolver",
	}

	c.AddCommand(
		p.NewResolverDeployCmd(),
		p.NewResolverDeleteCmd(),
	)

	return c
}
