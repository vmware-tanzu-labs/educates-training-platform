package installer

import (
	core "carvel.dev/kapp/pkg/kapp/cmd/core"
	"github.com/vmware-tanzu-labs/educates-training-platform/client-programs/pkg/cluster"
	"k8s.io/apimachinery/pkg/api/meta"
	"k8s.io/client-go/dynamic"
	"k8s.io/client-go/kubernetes"
)

type KappDepsFactoryImpl struct {
	clusterConfig *cluster.ClusterConfig
}

var _ core.DepsFactory = &KappDepsFactoryImpl{}

func NewKappDepsFactoryImpl(clusterConfig *cluster.ClusterConfig) *KappDepsFactoryImpl {
	return &KappDepsFactoryImpl{clusterConfig: clusterConfig}
}

// ConfigureWarnings implements core.DepsFactory.
func (k *KappDepsFactoryImpl) ConfigureWarnings(warnings bool) {
	// no-op
}

// CoreClient implements core.DepsFactory.
func (k *KappDepsFactoryImpl) CoreClient() (kubernetes.Interface, error) {
	return k.clusterConfig.GetClient()
}

// DynamicClient implements core.DepsFactory.
func (k *KappDepsFactoryImpl) DynamicClient(opts core.DynamicClientOpts) (dynamic.Interface, error) {
	return k.clusterConfig.GetDynamicClient()
}

func (k *KappDepsFactoryImpl) RESTMapper() (meta.RESTMapper, error) {
	// TODO: Implement this method
	return nil, nil
}
