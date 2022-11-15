// Copyright 2022 The Educates Authors.

package cmd

import (
	"github.com/spf13/cobra"
	"k8s.io/kubectl/pkg/util/templates"
)

func (p *ProjectInfo) NewDockerWorkshopCmdGroup() *cobra.Command {
	var c = &cobra.Command{
		Use:     "workshop",
		Aliases: []string{"workshops"},
		Short:   "Manage workshops in Docker",
	}

	// Use a command group as it allows us to dictate the order in which they
	// are displayed in the help message, as otherwise they are displayed in
	// sort order.

	commandGroups := templates.CommandGroups{
		{
			Message: "Available Commands:",
			Commands: []*cobra.Command{
				p.NewDockerWorkshopDeployCmd(),
				p.NewDockerWorkshopOpenCmd(),
				p.NewDockerWorkshopDeleteCmd(),
				p.NewDockerWorkshopListCmd(),
			},
		},
	}

	commandGroups.Add(c)

	templates.ActsAsRootCommand(c, []string{"options"}, commandGroups...)

	return c
}
