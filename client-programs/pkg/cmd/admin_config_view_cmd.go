package cmd

import (
	"fmt"

	"github.com/pkg/errors"
	"github.com/spf13/cobra"
	"gopkg.in/yaml.v2"

	"github.com/vmware-tanzu-labs/educates-training-platform/client-programs/pkg/config"
	"github.com/vmware-tanzu-labs/educates-training-platform/client-programs/pkg/secrets"
)

type AdminConfigViewOptions struct {
	WithLocalSecrets bool
	Config           string
}

func (o *AdminConfigViewOptions) Run() error {
	fullConfig, err := config.NewInstallationConfigFromFile(o.Config)

	if err != nil {
		return err
	}

	// This augments the installation config with the secrets that are cached locally
	if o.WithLocalSecrets {
		if secretName := secrets.LocalCachedSecretForIngressDomain(fullConfig.ClusterIngress.Domain); secretName != "" {
			fullConfig.ClusterIngress.TLSCertificateRef.Namespace = "educates-secrets"
			fullConfig.ClusterIngress.TLSCertificateRef.Name = secretName
		}

		if secretName := secrets.LocalCachedSecretForCertificateAuthority(fullConfig.ClusterIngress.Domain); secretName != "" {
			fullConfig.ClusterIngress.CACertificateRef.Namespace = "educates-secrets"
			fullConfig.ClusterIngress.CACertificateRef.Name = secretName
		}
	}

	configData, err := yaml.Marshal(&fullConfig)

	if err != nil {
		return errors.Wrap(err, "failed to generate installation config")
	}

	fmt.Print(string(configData))

	return nil
}

func (p *ProjectInfo) NewAdminConfigViewCmd() *cobra.Command {
	var o AdminConfigViewOptions

	var c = &cobra.Command{
		Args:  cobra.NoArgs,
		Use:   "view",
		Short: "View complete configuration",
		RunE:  func(_ *cobra.Command, _ []string) error { return o.Run() },
	}

	c.Flags().StringVar(
		&o.Config,
		"config",
		"",
		"path to the installation config file for Educates",
	)

	c.Flags().BoolVar(
		&o.WithLocalSecrets,
		"with-local-secrets",
		false,
		"show the configuration augmented with local secrets if they exist for the given domain",
	)

	return c
}
