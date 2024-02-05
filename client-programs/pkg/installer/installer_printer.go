package installer

import (
	"context"
	"fmt"
	"sync"

	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/client-go/kubernetes"
	"k8s.io/client-go/rest"
)

// type InstallerLogger interface {
// }

type InstallerPrinterImpl struct {
	printTargetOnce *sync.Once
}

func NewInstallerPrinterImpl() *InstallerPrinterImpl {
	return &InstallerPrinterImpl{
		printTargetOnce: &sync.Once{}}
}

func (f *InstallerPrinterImpl) printTarget(config *rest.Config) {
	f.printTargetOnce.Do(func() {
		nodesDesc := f.summarizeNodes(config)
		if len(nodesDesc) > 0 {
			nodesDesc = fmt.Sprintf(" (nodes: %s)", nodesDesc)
		}
		fmt.Printf("Target cluster '%s'%s", config.Host, nodesDesc)
	})
}

func (f *InstallerPrinterImpl) summarizeNodes(config *rest.Config) string {
	clientset, err := kubernetes.NewForConfig(config)
	if err != nil {
		return ""
	}

	nodes, err := clientset.CoreV1().Nodes().List(context.TODO(), metav1.ListOptions{})
	if err != nil {
		return ""
	}

	switch len(nodes.Items) {
	case 0:
		return ""

	case 1:
		return nodes.Items[0].Name

	default:
		oldestNode := nodes.Items[0]
		for _, node := range nodes.Items {
			if node.CreationTimestamp.Before(&oldestNode.CreationTimestamp) {
				oldestNode = node
			}
		}
		return fmt.Sprintf("%s, %d+", oldestNode.Name, len(nodes.Items)-1)
	}
}
