/*
Copyright © 2022 The Educates Authors.
*/
package cmd

import (
	"github.com/spf13/cobra"

	"github.com/vmware-tanzu-labs/educates-training-platform/client-programs/pkg/cluster"
)

func NewClusterStartCmd() *cobra.Command {
	var c = &cobra.Command{
		Args:  cobra.NoArgs,
		Use:   "start",
		Short: "Start the local Kind cluster",
		RunE: func(_ *cobra.Command, _ []string) error {
			c := cluster.NewKindClusterConfig("")

			return c.StartCluster()
		},
	}

	return c
}
