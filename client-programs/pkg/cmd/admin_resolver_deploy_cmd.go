package cmd

import (
	"github.com/spf13/cobra"

	"github.com/vmware-tanzu-labs/educates-training-platform/client-programs/pkg/config"
	"github.com/vmware-tanzu-labs/educates-training-platform/client-programs/pkg/resolver"
)

type AdminResolverDeployOptions struct {
	Config string
	Domain string
}

func (o *AdminResolverDeployOptions) Run() error {
	var fullConfig *config.InstallationConfig
	var err error = nil

	if o.Config != "" {
		fullConfig, err = config.NewInstallationConfigFromFile(o.Config)
	} else {
		fullConfig, err = config.NewDefaultInstallationConfig()
	}

	if err != nil {
		return err
	}

	if o.Domain != "" {
		fullConfig.ClusterIngress.Domain = o.Domain
	}

	return resolver.DeployResolver(fullConfig.ClusterIngress.Domain, fullConfig.LocalDNSResolver.TargetAddress, fullConfig.LocalDNSResolver.ExtraDomains)
}

func (p *ProjectInfo) NewAdminResolverDeployCmd() *cobra.Command {
	var o AdminResolverDeployOptions

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
