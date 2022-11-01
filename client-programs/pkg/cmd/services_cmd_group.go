// Copyright 2022 The Educates Authors.

package cmd

import (
	"github.com/spf13/cobra"
)

func (p *ProjectInfo) NewServicesCmdGroup() *cobra.Command {
	var c = &cobra.Command{
		Use:   "cluster-essentials",
		Short: "Install cluster services",
	}

	c.AddCommand(
		p.NewServicesDeployCmd(),
		p.NewServicesDeleteCmd(),
	)

	return c
}
