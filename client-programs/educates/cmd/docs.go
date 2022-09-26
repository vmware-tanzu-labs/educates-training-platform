/*
Copyright © 2022 The Educates Authors.
*/
package cmd

import (
	"github.com/spf13/cobra"
)

func NewDocsCmd() *cobra.Command {
	var docsCmd = &cobra.Command{
		Use:   "docs",
		Short: "Access package documentation",
	}

	docsCmd.AddCommand(
		NewDocsOpenCmd(),
	)

	return docsCmd
}
