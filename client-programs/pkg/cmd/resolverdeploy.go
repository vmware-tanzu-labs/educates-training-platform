// Copyright 2022 The Educates Authors.

package cmd

import (
	"github.com/spf13/cobra"

	"github.com/vmware-tanzu-labs/educates-training-platform/client-programs/pkg/config"
	"github.com/vmware-tanzu-labs/educates-training-platform/client-programs/pkg/resolver"
)

type ResolverDeployOptions struct {
	Config string
	Domain string
}

func (o *ResolverDeployOptions) Run() error {
	config, err := config.NewInstallationConfigFromFile(o.Config)

	if err != nil {
		return err
	}

	if o.Domain != "" {
		config.ClusterIngress.Domain = o.Domain
	}

	return resolver.DeployResolver(config.ClusterIngress.Domain)
}

func NewResolverDeployCmd() *cobra.Command {
	var o ResolverDeployOptions

	var c = &cobra.Command{
		Args:  cobra.NoArgs,
		Use:   "deploy",
		Short: "Deploys a local DNS resolver",
		RunE:  func(_ *cobra.Command, _ []string) error { return o.Run() },
	}

	c.Flags().StringVar(
		&o.Config,
		"config",
		"",
		"path to the installation config file for Educates",
	)
	c.Flags().StringVar(
		&o.Domain,
		"domain",
		"",
		"wildcard ingress subdomain name for Educates",
	)

	return c
}
