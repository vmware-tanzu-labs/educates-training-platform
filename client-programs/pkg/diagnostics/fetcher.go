package diagnostics

import (
	"context"
	"io"
	"os"
	"path/filepath"
	"strings"

	"github.com/vmware-tanzu-labs/educates-training-platform/client-programs/pkg/cluster"
	v1 "k8s.io/api/core/v1"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/runtime/schema"
	"k8s.io/cli-runtime/pkg/printers"
)

var workshopResource = schema.GroupVersionResource{Group: "training.educates.dev", Version: "v1beta1", Resource: "workshops"}
var trainingportalResource = schema.GroupVersionResource{Group: "training.educates.dev", Version: "v1beta1", Resource: "trainingportals"}
var workshopsessionsResource = schema.GroupVersionResource{Group: "training.educates.dev", Version: "v1beta1", Resource: "workshopsessions"}
var workshoprequestsResource = schema.GroupVersionResource{Group: "training.educates.dev", Version: "v1beta1", Resource: "workshoprequests"}
var workshopenvironmentsResource = schema.GroupVersionResource{Group: "training.educates.dev", Version: "v1beta1", Resource: "workshopenvironments"}
var workshopallocationsResource = schema.GroupVersionResource{Group: "training.educates.dev", Version: "v1beta1", Resource: "workshopallocations"}
var secretcopierResource = schema.GroupVersionResource{Group: "secrets.educates.dev", Version: "v1beta1", Resource: "secretcopiers"}
var secretinjectorsResource = schema.GroupVersionResource{Group: "secrets.educates.dev", Version: "v1beta1", Resource: "secretinjectors"}
var secretexportersResource = schema.GroupVersionResource{Group: "secrets.educates.dev", Version: "v1beta1", Resource: "secretexporters"}
var secretimportersResource = schema.GroupVersionResource{Group: "secrets.educates.dev", Version: "v1beta1", Resource: "secretimporters"}

type ClusterDiagnosticsFetcher struct {
	clusterConfig *cluster.ClusterConfig
	tempDir       string
}

func (c *ClusterDiagnosticsFetcher) getEducatesNamespaces() error {
	client, err := c.clusterConfig.GetClient()
	if err != nil {
		return err
	}

	namespaces, err := client.CoreV1().Namespaces().List(context.TODO(), metav1.ListOptions{
		// LabelSelector: "training.educates.dev/component",
	})
	if err != nil {
		return err
	}

	newFile, err := os.Create(filepath.Join(c.tempDir, "educates-namespaces.yaml"))
	if err != nil {
		return err
	}
	defer newFile.Close()

	y := printers.YAMLPrinter{}
	for _, object := range namespaces.Items {
		object.SetManagedFields(nil) // Remove managedFields from the object
		// We need to add the GroupVersionKind to the object, as it is not set by default. See: https://github.com/kubernetes-sigs/controller-runtime/issues/1517
		object.GetObjectKind().SetGroupVersionKind(schema.GroupVersionKind{Group: "", Version: "v1", Kind: "Namespace"})
		if err := y.PrintObj(&object, newFile); err != nil {
			return err
		}
	}

	return nil
}

// TODO: Print events in a more human readable format
func (c *ClusterDiagnosticsFetcher) getEducatesNamespacesEvents() error {
	client, err := c.clusterConfig.GetClient()
	if err != nil {
		return err
	}

	namespaces, err := client.CoreV1().Namespaces().List(context.TODO(), metav1.ListOptions{})
	if err != nil {
		return err
	}

	newFile, err := os.Create(filepath.Join(c.tempDir, "educates-events.yaml"))
	if err != nil {
		return err
	}
	defer newFile.Close()

	y := printers.YAMLPrinter{}
	for _, namespace := range namespaces.Items {
		if !strings.HasPrefix(namespace.Labels["kubernetes.io/metadata.name"], "educates") {
			continue
		}
		events, err := client.CoreV1().Events(namespace.Name).List(context.TODO(), metav1.ListOptions{
			// LabelSelector: "training.educates.dev/component",
		})
		for _, object := range events.Items {
			object.SetManagedFields(nil) // Remove managedFields from the object
			// We need to add the GroupVersionKind to the object, as it is not set by default. See: https://github.com/kubernetes-sigs/controller-runtime/issues/1517
			object.GetObjectKind().SetGroupVersionKind(schema.GroupVersionKind{Group: "events.k8s.io", Version: "v1", Kind: "Event"})
			if err := y.PrintObj(&object, newFile); err != nil {
				return err
			}
		}
		if err != nil {
			return err
		}
	}

	return nil
}

func (c *ClusterDiagnosticsFetcher) fetchDynamicallyResources(res schema.GroupVersionResource, file string) error {
	dynamicClient, err := c.clusterConfig.GetDynamicClient()
	if err != nil {
		return err
	}
	dynClient := dynamicClient.Resource(res)

	objectList, err := dynClient.List(context.TODO(), metav1.ListOptions{})
	if err != nil {
		return err
	}

	newFile, err := os.Create(filepath.Join(c.tempDir, file))
	if err != nil {
		return err
	}
	defer newFile.Close()

	y := printers.YAMLPrinter{}
	for _, object := range objectList.Items {
		object.SetManagedFields(nil) // Remove managedFields from the object
		if err := y.PrintObj(&object, newFile); err != nil {
			return err
		}
	}

	return nil
}

func (c *ClusterDiagnosticsFetcher) fetchLogsForDeployment(deploymentName, namespaceName, fileName string) error {
	client, err := c.clusterConfig.GetClient()
	if err != nil {
		return err
	}

	pods, err := client.CoreV1().Pods(namespaceName).List(context.TODO(), metav1.ListOptions{
		LabelSelector: "deployment=" + deploymentName,
	})
	if err != nil {
		return err
	}

	logFile, err := os.Create(filepath.Join(c.tempDir, fileName))
	if err != nil {
		return err
	}
	defer logFile.Close()

	for _, pod := range pods.Items {
		req := client.CoreV1().Pods(pod.Namespace).GetLogs(pod.Name, &v1.PodLogOptions{})
		podLogs, err := req.Stream(context.TODO())
		if err != nil {
			return err
		}
		defer podLogs.Close()

		_, err = io.Copy(logFile, podLogs)
		if err != nil {
			return err
		}
	}

	return nil
}
