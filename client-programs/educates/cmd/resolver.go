/*
Copyright © 2022 The Educates Authors.
*/
package cmd

import (
	"github.com/spf13/cobra"
)

func NewResolverCmd() *cobra.Command {
	var resolverCmd = &cobra.Command{
		Use:   "dns-resolver",
		Short: "Manage local DNS resolver",
	}

	resolverCmd.AddCommand(
		NewResolverDeleteCmd(),
		NewResolverDeployCmd(),
	)

	return resolverCmd
}
