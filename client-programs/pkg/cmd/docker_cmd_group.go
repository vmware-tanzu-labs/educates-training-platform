package cmd

import (
	"github.com/spf13/cobra"
	"k8s.io/kubectl/pkg/util/templates"
)

func (p *ProjectInfo) NewDockerCmdGroup() *cobra.Command {
	var c = &cobra.Command{
		Use:   "docker",
		Short: "Tools for deploying workshops to Docker",
	}

	// Use a command group as it allows us to dictate the order in which they
	// are displayed in the help message, as otherwise they are displayed in
	// sort order.

	commandGroups := templates.CommandGroups{
		{
			Message: "Available Commands:",
			Commands: []*cobra.Command{
				p.NewDockerWorkshopCmdGroup(),
				p.NewDockerExtensionCmdGroup(),
			},
		},
	}

	commandGroups.Add(c)

	templates.ActsAsRootCommand(c, []string{"--help"}, commandGroups...)

	return c
}
