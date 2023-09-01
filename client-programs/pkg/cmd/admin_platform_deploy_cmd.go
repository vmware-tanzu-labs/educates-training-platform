package cmd

import (
	"github.com/spf13/cobra"

	"github.com/vmware-tanzu-labs/educates-training-platform/client-programs/pkg/cluster"
	"github.com/vmware-tanzu-labs/educates-training-platform/client-programs/pkg/config"
	"github.com/vmware-tanzu-labs/educates-training-platform/client-programs/pkg/operators"
)

type AdminPlatformDeployOptions struct {
	Config     string
	Kubeconfig string
	Provider   string
	Domain     string
	Version    string
}

func (o *AdminPlatformDeployOptions) Run() error {
	fullConfig, err := config.NewInstallationConfigFromFile(o.Config)

	if err != nil {
		return err
	}

	if o.Domain != "" {
		fullConfig.ClusterIngress.Domain = o.Domain

		fullConfig.ClusterIngress.TLSCertificate = config.TLSCertificateConfig{}

		fullConfig.ClusterIngress.TLSCertificateRef.Namespace = ""
		fullConfig.ClusterIngress.TLSCertificateRef.Name = ""
	}

	if secretName := CachedSecretForIngressDomain(fullConfig.ClusterIngress.Domain); secretName != "" {
		fullConfig.ClusterIngress.TLSCertificateRef.Namespace = "educates-secrets"
		fullConfig.ClusterIngress.TLSCertificateRef.Name = secretName
	}

	if secretName := CachedSecretForCertificateAuthority(fullConfig.ClusterIngress.Domain); secretName != "" {
		fullConfig.ClusterIngress.CACertificateRef.Namespace = "educates-secrets"
		fullConfig.ClusterIngress.CACertificateRef.Name = secretName
	}

	fullConfig.ClusterInfrastructure.Provider = o.Provider

	clusterConfig := cluster.NewClusterConfig(o.Kubeconfig)

	platformConfig := config.TrainingPlatformConfig{
		ClusterSecurity:   fullConfig.ClusterSecurity,
		ClusterRuntime:    fullConfig.ClusterRuntime,
		ClusterIngress:    fullConfig.ClusterIngress,
		SessionCookies:    fullConfig.SessionCookies,
		ClusterStorage:    fullConfig.ClusterStorage,
		ClusterSecrets:    fullConfig.ClusterSecrets,
		TrainingPortal:    fullConfig.TrainingPortal,
		WorkshopSecurity:  fullConfig.WorkshopSecurity,
		ImageRegistry:     fullConfig.ImageRegistry,
		ImageVersions:     fullConfig.ImageVersions,
		DockerDaemon:      fullConfig.DockerDaemon,
		ClusterNetwork:    fullConfig.ClusterNetwork,
		WorkshopAnalytics: fullConfig.WorkshopAnalytics,
		WebsiteStyling:    fullConfig.WebsiteStyling,
	}

	return operators.DeployOperators(o.Version, clusterConfig, &platformConfig)
}

func (p *ProjectInfo) NewAdminPlatformDeployCmd() *cobra.Command {
	var o AdminPlatformDeployOptions

	var c = &cobra.Command{
		Args:  cobra.NoArgs,
		Use:   "deploy",
		Short: "Deploy platform operators",
		RunE:  func(_ *cobra.Command, _ []string) error { return o.Run() },
	}

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
		&o.Provider,
		"provider",
		"kind",
		"infastructure provider deployment is being made to",
	)
	c.Flags().StringVar(
		&o.Domain,
		"domain",
		"",
		"wildcard ingress subdomain name for Educates",
	)
	c.Flags().StringVar(
		&o.Version,
		"version",
		p.Version,
		"version to be installed",
	)

	return c
}
