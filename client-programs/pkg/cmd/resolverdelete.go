/*
Copyright © 2022 The Educates Authors.
*/
package cmd

import (
	"github.com/spf13/cobra"

	"github.com/vmware-tanzu-labs/educates-training-platform/client-programs/pkg/resolver"
)

func NewResolverDeleteCmd() *cobra.Command {
	var c = &cobra.Command{
		Args:  cobra.NoArgs,
		Use:   "delete",
		Short: "Deletes the local DNS resolver",
		RunE:  func(_ *cobra.Command, _ []string) error { return resolver.DeleteResolver() },
	}

	return c
}
