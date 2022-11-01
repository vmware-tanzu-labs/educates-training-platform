// Copyright 2022 The Educates Authors.

package cmd

import (
	"os"
	"path"

	"github.com/adrg/xdg"
	"github.com/spf13/cobra"
)

func (p *ProjectInfo) NewAdminConfigResetCmd() *cobra.Command {
	var c = &cobra.Command{
		Args:  cobra.NoArgs,
		Use:   "reset",
		Short: "Reset default configuration",
		RunE: func(_ *cobra.Command, _ []string) error {
			configFileDir := path.Join(xdg.DataHome, "educates")
			valuesFile := path.Join(configFileDir, "values.yaml")

			os.Remove(valuesFile)

			return nil
		},
	}

	return c
}
