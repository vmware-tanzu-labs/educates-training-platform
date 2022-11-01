// Copyright 2022 The Educates Authors.

package cmd

import (
	"github.com/spf13/cobra"
)

func (p *ProjectInfo) NewDockerCmd() *cobra.Command {
	var c = &cobra.Command{
		Use:   "docker-daemon",
		Short: "Manage workshops on Docker",
	}

	c.AddCommand(
		p.NewDockerWorkshopDeployCmd(),
		p.NewDockerWorkshopOpenCmd(),
		p.NewDockerWorkshopDeleteCmd(),
		p.NewDockerWorkshopsListCmd(),
	)

	return c
}
