package cluster

import (
	"os"

	"github.com/pkg/errors"
	"k8s.io/client-go/dynamic"
	"k8s.io/client-go/kubernetes"
	"k8s.io/client-go/rest"
	"k8s.io/client-go/tools/clientcmd"
	clientcmdapi "k8s.io/client-go/tools/clientcmd/api"
)

type ClusterConfig struct {
	Kubeconfig string
}

func NewClusterConfig(kubeconfig string) *ClusterConfig {
	return &ClusterConfig{kubeconfig}
}

func GetConfig(masterURL, kubeconfigPath string) (*rest.Config, error) {
	envVarName := clientcmd.RecommendedConfigPathEnvVar

	if kubeconfigPath == "" && masterURL == "" && os.Getenv(envVarName) == "" {
		// No explicit overrides so attempt to use in cluster config first.

		kubeconfig, err := rest.InClusterConfig()

		if err == nil {
			return kubeconfig, nil
		}
	}

	if kubeconfigPath != "" {
		if _, err := os.Stat(kubeconfigPath); os.IsNotExist(err) {
			// Only use override for kubeconfig file if it actually exists.

			kubeconfigPath = ""
		}
	}

	loadingRules := clientcmd.NewDefaultClientConfigLoadingRules()
	loadingRules.ExplicitPath = kubeconfigPath
	configOverrides := &clientcmd.ConfigOverrides{ClusterInfo: clientcmdapi.Cluster{Server: masterURL}}

	return clientcmd.NewNonInteractiveDeferredLoadingClientConfig(loadingRules, configOverrides).ClientConfig()
}

func (o *ClusterConfig) GetClient() (*kubernetes.Clientset, error) {
	config, err := GetConfig("", o.Kubeconfig)

	if err != nil {
		return nil, errors.Wrap(err, "unable to build client config")
	}

	return kubernetes.NewForConfig(config)
}

func (o *ClusterConfig) GetDynamicClient() (dynamic.Interface, error) {
	config, err := GetConfig("", o.Kubeconfig)

	if err != nil {
		return nil, errors.Wrap(err, "unable to build client config")
	}

	return dynamic.NewForConfig(config)
}

func KubeconfigPath(override string, fallback string) string {
	if override != "" {
		return override
	}

	// envvar := os.Getenv("KUBECONFIG")

	// if envvar != "" {
	// 	return envvar
	// }

	return fallback
}
