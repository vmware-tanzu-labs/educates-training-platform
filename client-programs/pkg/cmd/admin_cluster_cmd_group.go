package cmd

import (
	"github.com/spf13/cobra"
	"k8s.io/kubectl/pkg/util/templates"
)

func (p *ProjectInfo) NewAdminClusterCmdGroup() *cobra.Command {
	var c = &cobra.Command{
		Use:   "cluster",
		Short: "Manage local Kubernetes cluster",
	}

	// Use a command group as it allows us to dictate the order in which they
	// are displayed in the help message, as otherwise they are displayed in
	// sort order.

	commandGroups := templates.CommandGroups{
		{
			Message: "Available Commands:",
			Commands: []*cobra.Command{
				p.NewAdminClusterCreateCmd(),
				p.NewAdminClusterStartCmd(),
				p.NewAdminClusterStopCmd(),
				p.NewAdminClusterDeleteCmd(),
				p.NewAdminInstallCmd(),
			},
		},
	}

	commandGroups.Add(c)

	templates.ActsAsRootCommand(c, []string{"--help"}, commandGroups...)

	return c
}
