package cmd

import (
	"github.com/spf13/cobra"
	"k8s.io/kubectl/pkg/util/templates"
)

func (p *ProjectInfo) NewClusterWorkshopCmdGroup() *cobra.Command {
	var c = &cobra.Command{
		Use:     "workshop",
		Aliases: []string{"workshops"},
		Short:   "Manage workshops in Kubernetes",
	}

	// Use a command group as it allows us to dictate the order in which they
	// are displayed in the help message, as otherwise they are displayed in
	// sort order.

	commandGroups := templates.CommandGroups{
		{
			Message: "Available Commands:",
			Commands: []*cobra.Command{
				p.NewClusterWorkshopDeployCmd(),
				p.NewClusterWorkshopListCmd(),
				p.NewClusterWorkshopServeCmd(),
				p.NewClusterWorkshopRequestCmd(),
				p.NewClusterWorkshopUpdateCmd(),
				p.NewClusterWorkshopDeleteCmd(),
			},
		},
	}

	commandGroups.Add(c)

	templates.ActsAsRootCommand(c, []string{"--help"}, commandGroups...)

	return c
}
