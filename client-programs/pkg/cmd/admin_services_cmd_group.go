// Copyright 2022 The Educates Authors.

package cmd

import (
	"github.com/spf13/cobra"
	"k8s.io/kubectl/pkg/util/templates"
)

func (p *ProjectInfo) NewAdminServicesCmdGroup() *cobra.Command {
	var c = &cobra.Command{
		Use:   "services",
		Short: "Install cluster services",
	}

	// Use a command group as it allows us to dictate the order in which they
	// are displayed in the help message, as otherwise they are displayed in
	// sort order.

	commandGroups := templates.CommandGroups{
		{
			Message: "Available Commands:",
			Commands: []*cobra.Command{
				p.NewAdminServicesDeployCmd(),
				p.NewAdminServicesDeleteCmd(),
			},
		},
	}

	commandGroups.Add(c)

	templates.ActsAsRootCommand(c, []string{"options"}, commandGroups...)

	return c
}
