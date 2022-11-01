// Copyright 2022 The Educates Authors.

package cmd

import (
	"github.com/spf13/cobra"
	"k8s.io/kubectl/pkg/util/templates"
)

/*
Create Cobra command group for commands related to documentation.

NOTE: Using a command group here in case later on we want to support having the
docs bundled in the binary, but still want to open hosted documentation, or have
ability to download a newer version of development version of docs to local host
for offline viewing.
*/
func (p *ProjectInfo) NewProjectDocsCmdGroup() *cobra.Command {
	var c = &cobra.Command{
		Use:   "docs",
		Short: "Access Educates project documentation",
	}

	// Use a command group as it allows us to dictate the order in which they
	// are displayed in the help message, as otherwise they are displayed in
	// sort order.

	commandGroups := templates.CommandGroups{
		{
			Message: "Available Commands:",
			Commands: []*cobra.Command{
				p.NewProjectDocsOpenCmd(),
			},
		},
	}

	commandGroups.Add(c)

	templates.ActsAsRootCommand(c, []string{"options"}, commandGroups...)

	return c
}
