// Copyright 2022 The Educates Authors.

package cmd

import (
	"github.com/spf13/cobra"
)

func (info *ProjectInfo) NewVersionCmd() *cobra.Command {
	var c = &cobra.Command{
		Args:  cobra.NoArgs,
		Use:   "version",
		Short: "Display the version of Educates",
		RunE: func(cmd *cobra.Command, _ []string) error {
			cmd.Println(info.Version)
			return nil
		},
	}

	return c
}
