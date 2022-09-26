/*
Copyright © 2022 The Educates Authors.
*/
package cluster

import (
	"bytes"
	_ "embed"
	"fmt"
	"html/template"
	"os"
	"path/filepath"
	"time"

	"github.com/pkg/errors"
	"golang.org/x/exp/slices"
	"sigs.k8s.io/kind/pkg/cluster"
	"sigs.k8s.io/kind/pkg/cmd"

	"github.com/vmware-tanzu-labs/educates-training-platform/client-programs/educates/pkg/config"
)

type KindClusterConfig struct {
	ClusterConfig
}

func NewKindClusterConfig(kubeconfig string) *KindClusterConfig {
	fallback := ""

	home, err := os.UserHomeDir()

	if err == nil {
		fallback = filepath.Join(home, ".kube", "config")
	}

	return &KindClusterConfig{ClusterConfig{KubeconfigPath(kubeconfig, fallback)}}
}

//go:embed kindclusterconfig.yaml.tpl
var clusterConfigTemplateData string

func (o *KindClusterConfig) CreateCluster(config *config.InstallationConfig, image string) error {
	provider := cluster.NewProvider(
		cluster.ProviderWithLogger(cmd.NewLogger()),
	)

	clusters, err := provider.List()

	if err != nil {
		return errors.Wrap(err, "unable to get list of clusters")
	}

	if slices.Contains(clusters, "educates") {
		return errors.New("cluster for Educates already exists")
	}

	clusterConfigTemplate, err := template.New("kind-cluster-config").Parse(clusterConfigTemplateData)

	if err != nil {
		return errors.Wrap(err, "failed to parse cluster config template")
	}

	var clusterConfigData bytes.Buffer

	err = clusterConfigTemplate.Execute(&clusterConfigData, config)

	if err != nil {
		return errors.Wrap(err, "failed to generate cluster config")
	}

	if err := provider.Create(
		"educates",
		cluster.CreateWithRawConfig(clusterConfigData.Bytes()),
		cluster.CreateWithNodeImage(image),
		cluster.CreateWithWaitForReady(time.Duration(time.Duration(60)*time.Second)),
		cluster.CreateWithKubeconfigPath(o.Kubeconfig),
		cluster.CreateWithDisplayUsage(true),
		cluster.CreateWithDisplaySalutation(true),
	); err != nil {
		return errors.Wrap(err, "failed to create cluster")
	}

	return nil
}

func (o *KindClusterConfig) DeleteCluster() error {
	provider := cluster.NewProvider(
		cluster.ProviderWithLogger(cmd.NewLogger()),
	)

	fmt.Println("Deleting cluster educates ...")

	if err := provider.Delete("educates", o.Kubeconfig); err != nil {
		return errors.Wrapf(err, "failed to delete cluster")
	}

	return nil
}
