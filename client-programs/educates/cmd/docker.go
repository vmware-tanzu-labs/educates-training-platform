/*
Copyright © 2022 The Educates Authors.
*/
package cmd

import (
	"github.com/spf13/cobra"
)

func NewDockerCmd() *cobra.Command {
	var dockerCmd = &cobra.Command{
		Use:   "docker-daemon",
		Short: "Manage workshops on Docker",
	}

	dockerCmd.AddCommand(
		NewDockerWorkshopDeployCmd(),
		NewDockerWorkshopDeleteCmd(),
		NewDockerWorkshopsListCmd(),
	)

	return dockerCmd
}
