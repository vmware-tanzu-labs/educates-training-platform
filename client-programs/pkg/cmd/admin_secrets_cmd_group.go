package cmd

import (
	"github.com/spf13/cobra"
	"k8s.io/kubectl/pkg/util/templates"
)

func (p *ProjectInfo) NewAdminSecretsCmdGroup() *cobra.Command {
	var c = &cobra.Command{
		Use:   "secrets",
		Short: "Manage local secrets cache",
	}

	// Use a command group as it allows us to dictate the order in which they
	// are displayed in the help message, as otherwise they are displayed in
	// sort order.

	commandGroups := templates.CommandGroups{
		{
			Message: "Available Commands:",
			Commands: []*cobra.Command{
				p.NewAdminSecretsAddCmdGroup(),
				p.NewAdminSecretsListCmd(),
				p.NewAdminSecretsExportCmd(),
				p.NewAdminSecretsImportCmd(),
				p.NewAdminSecretsSyncCmd(),
				p.NewAdminSecretsRemoveCmd(),
			},
		},
	}

	commandGroups.Add(c)

	templates.ActsAsRootCommand(c, []string{"--help"}, commandGroups...)

	return c
}
