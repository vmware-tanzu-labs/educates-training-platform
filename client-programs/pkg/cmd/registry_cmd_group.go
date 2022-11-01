// Copyright 2022 The Educates Authors.

package cmd

import (
	"github.com/spf13/cobra"
)

func (p *ProjectInfo) NewRegistryCmdGroup() *cobra.Command {
	var c = &cobra.Command{
		Use:   "image-registry",
		Short: "Manage local image registry",
	}

	c.AddCommand(
		p.NewRegistryDeployCmd(),
		p.NewRegistryDeleteCmd(),
	)

	return c
}
