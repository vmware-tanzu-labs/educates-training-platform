package cmd

import (
	"github.com/spf13/cobra"
	"k8s.io/kubectl/pkg/util/templates"
)

func (p *ProjectInfo) NewAdminConfigCmdGroup() *cobra.Command {
	var c = &cobra.Command{
		Use:   "config",
		Short: "Manage configuration files",
	}

	// Use a command group as it allows us to dictate the order in which they
	// are displayed in the help message, as otherwise they are displayed in
	// sort order.

	commandGroups := templates.CommandGroups{
		{
			Message: "Available Commands:",
			Commands: []*cobra.Command{
				p.NewAdminConfigEditCmd(),
				p.NewAdminConfigViewCmd(),
				p.NewAdminConfigResetCmd(),
			},
		},
	}

	commandGroups.Add(c)

	templates.ActsAsRootCommand(c, []string{"--help"}, commandGroups...)

	return c
}
