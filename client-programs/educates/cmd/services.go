/*
Copyright © 2022 The Educates Authors.
*/
package cmd

import (
	"github.com/spf13/cobra"
)

func NewServicesCmd() *cobra.Command {
	var servicesCmd = &cobra.Command{
		Use:   "services",
		Short: "Manage cluster services",
	}

	servicesCmd.AddCommand(
		NewServicesDeleteCmd(),
		NewServicesDeployCmd(),
	)

	return servicesCmd
}
