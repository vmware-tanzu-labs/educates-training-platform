package cmd

import (
	"github.com/spf13/cobra"
	"k8s.io/kubectl/pkg/util/templates"
)

func (p *ProjectInfo) NewLocalConfigCmdGroup() *cobra.Command {
	var c = &cobra.Command{
		Use:   "config",
		Short: "Manage local configuration files",
		Long: "Manage local configuration files. This configuration will be used when creating a local cluster " +
			"using the 'educates local cluster create' command. By default it will use the nip.io wildcard domain " +
			"and Kind as the provider." + "\n" +
			"This configuration is saved in the Educates home directory.",
	}

	// Use a command group as it allows us to dictate the order in which they
	// are displayed in the help message, as otherwise they are displayed in
	// sort order.

	commandGroups := templates.CommandGroups{
		{
			Message: "Available Commands:",
			Commands: []*cobra.Command{
				p.NewLocalConfigEditCmd(),
				p.NewLocalConfigViewCmd(),
				p.NewLocalConfigResetCmd(),
			},
		},
	}

	commandGroups.Add(c)

	templates.ActsAsRootCommand(c, []string{"--help"}, commandGroups...)

	return c
}
