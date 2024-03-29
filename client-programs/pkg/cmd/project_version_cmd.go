package cmd

import (
	"github.com/spf13/cobra"
)

/*
Create Cobra command object for displaying Educates version.
*/
func (p *ProjectInfo) NewProjectVersionCmd() *cobra.Command {
	var c = &cobra.Command{
		Args:  cobra.NoArgs,
		Use:   "version",
		Short: "Display the version of Educates being used",
		RunE: func(cmd *cobra.Command, _ []string) error {
			cmd.Println(p.Version)
			return nil
		},
	}

	return c
}
