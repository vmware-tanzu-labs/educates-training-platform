// Copyright 2022 The Educates Authors.

package cmd

import (
	"github.com/spf13/cobra"
)

func (info *ProjectInfo) NewServicesCmd() *cobra.Command {
	var servicesCmd = &cobra.Command{
		Use:   "cluster-essentials",
		Short: "Install cluster services",
	}

	servicesCmd.AddCommand(
		info.NewServicesDeployCmd(),
		NewServicesDeleteCmd(),
	)

	return servicesCmd
}
