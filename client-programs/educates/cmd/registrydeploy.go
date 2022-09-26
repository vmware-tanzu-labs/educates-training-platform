/*
Copyright © 2022 The Educates Authors.
*/
package cmd

import (
	"github.com/spf13/cobra"

	"github.com/vmware-tanzu-labs/educates-training-platform/client-programs/educates/pkg/registry"
)

func NewRegistryDeployCmd() *cobra.Command {
	var c = &cobra.Command{
		Args:  cobra.NoArgs,
		Use:   "deploy",
		Short: "Deploys a local image registry",
		RunE:  func(_ *cobra.Command, _ []string) error { return registry.DeployRegistry() },
	}

	return c
}
