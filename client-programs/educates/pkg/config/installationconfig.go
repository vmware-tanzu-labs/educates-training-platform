/*
Copyright © 2022 The Educates Authors.
*/
package config

import (
	"fmt"
	"os"
	"path"

	"github.com/adrg/xdg"
	"github.com/pkg/errors"
	"gopkg.in/yaml.v2"
)

type VolumeMountConfig struct {
	HostPath      string `yaml:"hostPath"`
	ContainerPath string `yaml:"containerPath"`
	ReadOnly      bool   `yaml:"readOnly,omitempty"`
}

type LocalKindClusterConfig struct {
	ListenAddress string              `yaml:"listenAddress,omitempty"`
	VolumeMounts  []VolumeMountConfig `yaml:"volumeMounts,omitempty"`
}

type ClusterInfrastructureConfig struct {
	Provider string `yaml:"provider"`
}

type PackageConfig struct {
	Enabled  bool                   `yaml:"enabled"`
	Settings map[string]interface{} `yaml:"settings"`
}
type ClusterPackagesConfig struct {
	Contour        PackageConfig `yaml:"contour"`
	Kyverno        PackageConfig `yaml:"kyverno"`
	MetaController PackageConfig `yaml:"metacontroller,omitempty"`
}

type TLSCertificateConfig struct {
	Certificate string `yaml:"tls.crt"`
	PrivateKey  string `yaml:"tls.key"`
}

type TLSCertificateRefConfig struct {
	Namespace string `yaml:"namespace"`
	Name      string `yaml:"name"`
}

type ClusterIngressConfig struct {
	Domain            string                  `yaml:"domain"`
	Class             string                  `yaml:"class,omitempty"`
	Protocol          string                  `yaml:"protocol,omitempty"`
	TLSCertificate    TLSCertificateConfig    `yaml:"tlsCertificate,omitempty"`
	TLSCertificateRef TLSCertificateRefConfig `yaml:"tlsCertificateRef,omitempty"`
}

type ClusterStorageConfig struct {
	Class string `yaml:"class,omitempty"`
	User  int    `yaml:"user,omitempty"`
	Group int    `yaml:"group,omitempty"`
}

type ClusterSecurityConfig struct {
	PolicyEngine string `yaml:"policyEngine"`
}

type PullSecretRefConfig struct {
	Namespace string `yaml:"namespace"`
	Name      string `yaml:"name"`
}

type ClusterSecretsConfig struct {
	PullSecretRefs []PullSecretRefConfig
}

type UserCredentialsConfig struct {
	Username string `yaml:"username"`
	Password string `yaml:"password"`
}

type TrainingPortalCredentialsConfig struct {
	Admin UserCredentialsConfig `yaml:"admin,omitempty"`
	Robot UserCredentialsConfig `yaml:"robot,omitempty"`
}

type TrainingPortalConfig struct {
	Credentials TrainingPortalCredentialsConfig `yaml:"credentials,omitempty"`
}

type WorkshopSecurityConfig struct {
	RulesEngine string `yaml:"rulesEngine"`
}

type ImageRegistryConfig struct {
	Host      string `yaml:"host"`
	Namespace string `yaml:"namespace"`
}

type ImageVersionConfig struct {
	Name  string `yaml:"name"`
	Image string `yaml:"image"`
}

type ImageVersionsConfig struct {
	ImageVersions []ImageVersionConfig
}

type ProxyCacheConfig struct {
	RemoteURL string `yaml:"remoteURL"`
	Username  string `yaml:"username,omitempty"`
	Password  string `yaml:"password,omitempty"`
}
type DockerDaemonConfig struct {
	NetworkMTU int              `yaml:"networkMTU,omitempty"`
	Rootless   bool             `yaml:"rootless,omitempty"`
	Privileged bool             `yaml:"privileged,omitempty"`
	ProxyCache ProxyCacheConfig `yaml:"proxyCache,omitempty"`
}

type ClusterNetworkConfig struct {
	BlockCIDRS []string `yaml:"blockCIDRS"`
}

type GoogleAnayticsConfig struct {
	TrackingId string `yaml:"trackingId"`
}

type WebhookAnalyticsConfig struct {
	URL string `yaml:"url"`
}

type WorkshopAnalyticsConfig struct {
	Google  GoogleAnayticsConfig   `yaml:"google,omitempty"`
	Webhook WebhookAnalyticsConfig `yaml:"webhook,omitempty"`
}

type WebsiteStyleOverridesConfig struct {
	Script string `yaml:"script"`
	Style  string `yaml:"style"`
}

type WebsiteHTMLSnippetConfig struct {
	HTML string `yaml:"html"`
}

type WebsiteStylingConfig struct {
	WorkshopDashboard    WebsiteStyleOverridesConfig `yaml:"workshopDashboard,omitempty"`
	WorkshopInstructions WebsiteStyleOverridesConfig `yaml:"workshopInstructions,omitempty"`
	TrainingPortal       WebsiteStyleOverridesConfig `yaml:"trainingPortal,omitempty"`
	WorkshopStarted      WebsiteHTMLSnippetConfig    `yaml:"workshopStarted"`
	WorkshopFinished     WebsiteHTMLSnippetConfig    `yaml:"workshopFinished"`
}

type ClusterEssentialsConfig struct {
	ClusterInfrastructure ClusterInfrastructureConfig `yaml:"clusterInfrastructure,omitempty"`
	ClusterPackages       ClusterPackagesConfig       `yaml:"clusterPackages,omitempty"`
	ClusterSecurity       ClusterSecurityConfig       `yaml:"clusterSecurity,omitempty"`
}

type TrainingPlatformConfig struct {
	ClusterSecurity   ClusterSecurityConfig   `yaml:"clusterSecurity,omitempty"`
	ClusterIngress    ClusterIngressConfig    `yaml:"clusterIngress,omitempty"`
	ClusterStorage    ClusterStorageConfig    `yaml:"clusterStorage,omitempty"`
	ClusterSecrets    ClusterSecretsConfig    `yaml:"clusterSecrets,omitempty"`
	TrainingPortal    TrainingPortalConfig    `yaml:"trainingPortal,omitempty"`
	WorkshopSecurity  WorkshopSecurityConfig  `yaml:"workshopSecurity,omitempty"`
	ImageRegistry     ImageRegistryConfig     `yaml:"imageRegistry,omitempty"`
	ImageVersions     ImageVersionsConfig     `yaml:"imageVersions,omitempty"`
	DockerDaemon      DockerDaemonConfig      `yaml:"dockerDaemon,omitempty"`
	ClusterNetwork    ClusterNetworkConfig    `yaml:"clusterNetwork,omitempty"`
	WorkshopAnalytics WorkshopAnalyticsConfig `yaml:"workshopAnalytics,omitempty"`
	WebsiteStyling    WebsiteStylingConfig    `yaml:"websiteStyling,omitempty"`
}

type InstallationConfig struct {
	LocalKindCluster      LocalKindClusterConfig      `yaml:"localKindCluster,omitempty"`
	ClusterInfrastructure ClusterInfrastructureConfig `yaml:"clusterInfrastructure,omitempty"`
	ClusterPackages       ClusterPackagesConfig       `yaml:"clusterPackages,omitempty"`
	ClusterSecurity       ClusterSecurityConfig       `yaml:"clusterSecurity,omitempty"`
	ClusterIngress        ClusterIngressConfig        `yaml:"clusterIngress,omitempty"`
	ClusterStorage        ClusterStorageConfig        `yaml:"clusterStorage,omitempty"`
	ClusterSecrets        ClusterSecretsConfig        `yaml:"clusterSecrets,omitempty"`
	TrainingPortal        TrainingPortalConfig        `yaml:"trainingPortal,omitempty"`
	WorkshopSecurity      WorkshopSecurityConfig      `yaml:"workshopSecurity,omitempty"`
	ImageRegistry         ImageRegistryConfig         `yaml:"imageRegistry,omitempty"`
	ImageVersions         ImageVersionsConfig         `yaml:"imageVersions,omitempty"`
	DockerDaemon          DockerDaemonConfig          `yaml:"dockerDaemon,omitempty"`
	ClusterNetwork        ClusterNetworkConfig        `yaml:"clusterNetwork,omitempty"`
	WorkshopAnalytics     WorkshopAnalyticsConfig     `yaml:"workshopAnalytics,omitempty"`
	WebsiteStyling        WebsiteStylingConfig        `yaml:"websiteStyling,omitempty"`
}

func NewDefaultInstallationConfig() *InstallationConfig {
	localIPAddress, err := HostIP()

	if err != nil {
		localIPAddress = "127.0.0.1"
	}

	return &InstallationConfig{
		ClusterInfrastructure: ClusterInfrastructureConfig{
			Provider: "",
		},
		ClusterPackages: ClusterPackagesConfig{
			Contour: PackageConfig{
				Enabled: true,
			},
			Kyverno: PackageConfig{
				Enabled: true,
			},
		},
		ClusterSecurity: ClusterSecurityConfig{
			PolicyEngine: "kyverno",
		},
		ClusterIngress: ClusterIngressConfig{
			Domain: fmt.Sprintf("%s.nip.io", localIPAddress),
		},
		WorkshopSecurity: WorkshopSecurityConfig{
			RulesEngine: "kyverno",
		},
	}
}

func NewInstallationConfigFromFile(configFile string) (*InstallationConfig, error) {
	config := NewDefaultInstallationConfig()

	if configFile != "" {
		data, err := os.ReadFile(configFile)

		if err != nil {
			return nil, errors.Wrapf(err, "failed to read installation config file %s", configFile)
		}

		if err := yaml.Unmarshal(data, &config); err != nil {
			return nil, errors.Wrapf(err, "unable to parse installation config file %s", configFile)
		}
	} else {
		configFileDir := path.Join(xdg.DataHome, "educates")
		valuesFile := path.Join(configFileDir, "values.yaml")

		data, err := os.ReadFile(valuesFile)

		if err == nil && len(data) != 0 {
			if err := yaml.Unmarshal(data, &config); err != nil {
				return nil, errors.Wrapf(err, "unable to parse default config file %s", valuesFile)
			}
		}
	}

	return config, nil
}
