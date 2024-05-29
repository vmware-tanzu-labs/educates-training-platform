package cmd

import (
	"fmt"

	"github.com/pkg/errors"
	"github.com/spf13/cobra"

	"github.com/vmware-tanzu-labs/educates-training-platform/client-programs/pkg/cluster"
	"github.com/vmware-tanzu-labs/educates-training-platform/client-programs/pkg/config"
	"github.com/vmware-tanzu-labs/educates-training-platform/client-programs/pkg/installer"
	"github.com/vmware-tanzu-labs/educates-training-platform/client-programs/pkg/secrets"
	"github.com/vmware-tanzu-labs/educates-training-platform/client-programs/pkg/utils"
)

type AdminInstallOptions struct {
	KubeconfigOptions
	Delete              bool
	Config              string
	Provider            string
	DryRun              bool
	ShowPackagesValues  bool
	Version             string
	PackageRepository   string
	Verbose             bool
	WithLocalSecrets    bool
	skipImageResolution bool
	showDiff            bool
}

func (o *AdminInstallOptions) Run() error {
	fullConfig, err := config.NewInstallationConfigFromFile(o.Kubeconfig)

	if err != nil {
		return err
	}

	// This can be set in the config file if not provided via the command line
	if o.Provider != "" {
		fullConfig.ClusterInfrastructure.Provider = o.Provider
	}

	// Although ytt does some schema validation, we do some basic validation here
	if err := validateProvider(fullConfig.ClusterInfrastructure.Provider); err != nil {
		return err
	}

	installer := installer.NewInstaller()
	if o.Delete {
		clusterConfig := cluster.NewClusterConfig(o.Kubeconfig, o.Context)

		err := installer.Delete(fullConfig, clusterConfig, o.Verbose)

		if err != nil {
			return errors.Wrap(err, "educates could not be deleted")
		}

		fmt.Println("\nEducates has been deleted succesfully")
	} else {
		if o.WithLocalSecrets {
			if fullConfig.ClusterInfrastructure.Provider != "kind" {
				return errors.New("Local secrets are only supported for kind clusters provider")
			}

			if secretName := secrets.LocalCachedSecretForIngressDomain(fullConfig.ClusterIngress.Domain); secretName != "" {
				fullConfig.ClusterIngress.TLSCertificateRef.Namespace = "educates-secrets"
				fullConfig.ClusterIngress.TLSCertificateRef.Name = secretName
			}

			if secretName := secrets.LocalCachedSecretForCertificateAuthority(fullConfig.ClusterIngress.Domain); secretName != "" {
				fullConfig.ClusterIngress.CACertificateRef.Namespace = "educates-secrets"
				fullConfig.ClusterIngress.CACertificateRef.Name = secretName
			}

			if fullConfig.ClusterIngress.CACertificateRef.Name != "" || fullConfig.ClusterIngress.CACertificate.Certificate != "" {
				fullConfig.ClusterIngress.CANodeInjector.Enabled = utils.BoolPointer(true)
			}
		}

		if o.DryRun || o.ShowPackagesValues {
			if err = installer.DryRun(o.Version, o.PackageRepository, fullConfig, o.Verbose, o.ShowPackagesValues, o.skipImageResolution); err != nil {
				return errors.Wrap(err, "educates could not be installed")
			}
			return nil
		}

		clusterConfig, err := cluster.NewClusterConfigIfAvailable(o.Kubeconfig, o.Context)
		if err != nil {
			return err
		}

		client, err := clusterConfig.GetClient()
		if err != nil {
			return err
		}

		// This creates the educates-secrets namespace if it doesn't exist and creates the
		// wildcard and CA secrets in there
		if err = secrets.SyncLocalCachedSecretsToCluster(client); err != nil {
			return err
		}

		err = installer.Run(o.Version, o.PackageRepository, fullConfig, clusterConfig, o.Verbose, o.ShowPackagesValues, o.skipImageResolution, o.showDiff)
		if err != nil {
			return errors.Wrap(err, "educates could not be installed")
		}
		fmt.Println("\nEducates has been installed succesfully")
	}

	return nil
}

func validateProvider(provider string) error {
	switch provider {
	case "eks", "kind", "gke", "custom", "vcluster":
		return nil
	default:
		return errors.New("Invalid ClusterInsfrastructure Provider. Valid values are (eks, gke, kind, custom, vcluster)")
	}
}

func (p *ProjectInfo) NewAdminClusterInstallCmd() *cobra.Command {
	var o AdminInstallOptions

	var c = &cobra.Command{
		Args:  cobra.NoArgs,
		Use:   "install",
		Short: "Install Educates and related cluster services onto your cluster in an imperative manner",
		RunE: func(cmd *cobra.Command, _ []string) error {
			// We set the default of skipImageResolution to true if ShowPackagesValues is set and the user has not explicitly set it
			if o.ShowPackagesValues && !cmd.Flags().Changed("skip-image-resolution") {
				o.skipImageResolution = true
			}
			return o.Run()
		},
	}

	c.Flags().BoolVar(
		&o.Delete,
		"delete",
		false,
		"Should educates be deleted",
	)
	c.Flags().StringVar(
		&o.Config,
		"config",
		"",
		"path to the installation config file for Educates",
	)
	c.Flags().StringVar(
		&o.Kubeconfig,
		"kubeconfig",
		"",
		"kubeconfig file to use instead of $KUBECONFIG or $HOME/.kube/config",
	)
	c.Flags().StringVar(
		&o.Context,
		"context",
		"",
		"Context to use from Kubeconfig",
	)
	c.Flags().StringVar(
		&o.Provider,
		"provider",
		"",
		"infastructure provider deployment is being made to (eks, gke, kind, custom, vcluster)",
	)
	// TODO: Should we add domain (like admin_platform_deploy) or is it not needed?
	// c.Flags().StringVar(
	// 	&o.Domain,
	// 	"domain",
	// 	"",
	// 	"wildcard ingress subdomain name for Educates",
	// )
	c.Flags().BoolVar(
		&o.DryRun,
		"dry-run",
		false,
		"prints to stdout the yaml that would be deployed to the cluster",
	)
	c.Flags().BoolVar(
		&o.ShowPackagesValues,
		"show-packages-values",
		false,
		"prints values that will be passed to ytt to deploy all educates packages into the cluster",
	)
	c.Flags().BoolVar(
		&o.Verbose,
		"verbose",
		false,
		"print verbose output",
	)
	c.Flags().StringVar(
		&o.PackageRepository,
		"package-repository",
		p.ImageRepository,
		"image repository hosting package bundles",
	)
	c.Flags().StringVar(
		&o.Version,
		"version",
		p.Version,
		"version to be installed",
	)
	c.Flags().BoolVar(
		&o.WithLocalSecrets,
		"with-local-secrets",
		false,
		"show the configuration augmented with local secrets if they exist for the given domain",
	)
	c.Flags().BoolVar(
		&o.skipImageResolution,
		"skip-image-resolution",
		false,
		"skips resolution of referenced images so that all will be fetched from their original location",
	)
	c.Flags().BoolVar(
		&o.showDiff,
		"show-diff",
		false,
		"shows the diffs to be applied to the cluster when running the install",
	)
	c.MarkFlagRequired("config")

	return c
}
