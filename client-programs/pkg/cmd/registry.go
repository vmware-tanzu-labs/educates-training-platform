// Copyright 2022 The Educates Authors.

package cmd

import (
	"github.com/spf13/cobra"
)

func NewRegistryCmd() *cobra.Command {
	var registryCmd = &cobra.Command{
		Use:   "image-registry",
		Short: "Manage local image registry",
	}

	registryCmd.AddCommand(
		NewRegistryDeployCmd(),
		NewRegistryDeleteCmd(),
	)

	return registryCmd
}
