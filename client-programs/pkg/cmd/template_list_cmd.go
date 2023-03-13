// Copyright 2022-2023 The Educates Authors.

package cmd

import (
	"github.com/spf13/cobra"

	"github.com/vmware-tanzu-labs/educates-training-platform/client-programs/pkg/templates"
)

func (p *ProjectInfo) NewTemplateListCmd() *cobra.Command {
	var c = &cobra.Command{
		Args:  cobra.NoArgs,
		Use:   "list",
		Short: "List available workshop templates",
		RunE: func(cmd *cobra.Command, _ []string) error {
			for _, name := range templates.InternalTemplates() {
				cmd.Println(name)
			}

			return nil
		},
	}

	return c
}
