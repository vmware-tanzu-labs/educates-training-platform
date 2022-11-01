// Copyright 2022 The Educates Authors.

package cmd

import (
	"github.com/spf13/cobra"
	"k8s.io/kubectl/pkg/util/templates"
)

/*
Create Cobra command group for commands related to project.
*/
func (p *ProjectInfo) NewProjectCmdGroup() *cobra.Command {
	var c = &cobra.Command{
		Use:   "project",
		Short: "Tools for accessing information on Educates",
	}

	// Use a command group as it allows us to dictate the order in which they
	// are displayed in the help message, as otherwise they are displayed in
	// sort order.

	commandGroups := templates.CommandGroups{
		{
			Message: "Available Commands:",
			Commands: []*cobra.Command{
				p.NewProjectVersionCmd(),
				p.NewProjectDocsCmdGroup(),
			},
		},
	}

	commandGroups.Add(c)

	templates.ActsAsRootCommand(c, []string{"options"}, commandGroups...)

	return c
}
