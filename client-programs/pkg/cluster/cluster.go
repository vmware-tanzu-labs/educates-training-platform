// Copyright 2022-2023 The Educates Authors.

package cluster

import (
	"os"
	"path/filepath"

	"github.com/pkg/errors"
	"k8s.io/client-go/dynamic"
	"k8s.io/client-go/kubernetes"
	"k8s.io/client-go/tools/clientcmd"
)

type ClusterConfig struct {
	Kubeconfig string
}

func NewClusterConfig(kubeconfig string) *ClusterConfig {
	fallback := ""

	home, err := os.UserHomeDir()

	if err == nil {
		fallback = filepath.Join(home, ".kube", "config")
	}

	return &ClusterConfig{KubeconfigPath(kubeconfig, fallback)}
}

func (o *ClusterConfig) GetClient() (*kubernetes.Clientset, error) {
	config, err := clientcmd.BuildConfigFromFlags("", o.Kubeconfig)

	if err != nil {
		return nil, errors.Wrap(err, "unable to build client config")
	}

	return kubernetes.NewForConfig(config)
}

func (o *ClusterConfig) GetDynamicClient() (dynamic.Interface, error) {
	config, err := clientcmd.BuildConfigFromFlags("", o.Kubeconfig)

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
