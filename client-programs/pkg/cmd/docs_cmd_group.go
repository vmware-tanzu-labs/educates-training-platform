// Copyright 2022 The Educates Authors.

package cmd

import (
	"github.com/spf13/cobra"
)

/*
Create Cobra command group for commands related to documentation.

NOTE: Using a command group here in case later on we want to support having the
docs bundled in the binary, but still want to open hosted documentation, or have
ability to download a newer version of development version of docs to local host
for offline viewing.
*/
func (p *ProjectInfo) NewDocsCmdGroup() *cobra.Command {
	var c = &cobra.Command{
		Use:   "docs",
		Short: "Access package documentation",
	}

	c.AddCommand(
		p.NewDocsOpenCmd(),
	)

	return c
}
