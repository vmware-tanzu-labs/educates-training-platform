// Copyright 2022 The Educates Authors.

package cmd

import (
	"github.com/spf13/cobra"
)

func (p *ProjectInfo) NewClusterCmdGroup() *cobra.Command {
	var c = &cobra.Command{
		Use:   "kind-cluster",
		Short: "Manage local Kubernetes cluster",
	}

	c.AddCommand(
		p.NewClusterCreateCmd(),
		p.NewClusterStartCmd(),
		p.NewClusterStopCmd(),
		p.NewClusterDeleteCmd(),
	)

	return c
}
