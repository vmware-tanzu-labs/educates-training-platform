package installer

import (
	"github.com/vmware-tanzu-labs/educates-training-platform/client-programs/pkg/cluster"
	kappcore "github.com/vmware-tanzu/carvel-kapp/pkg/kapp/cmd/core"
	"k8s.io/client-go/dynamic"
	"k8s.io/client-go/kubernetes"
)

type KappDepsFactoryImpl struct {
	clusterConfig *cluster.ClusterConfig
}

var _ kappcore.DepsFactory = &KappDepsFactoryImpl{}

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
func (k *KappDepsFactoryImpl) DynamicClient(opts kappcore.DynamicClientOpts) (dynamic.Interface, error) {
	return k.clusterConfig.GetDynamicClient()
}
