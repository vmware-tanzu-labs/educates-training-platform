// Copyright 2022 The Educates Authors.

package cmd

import (
	"context"
	"fmt"
	"os"
	"text/tabwriter"

	"github.com/pkg/errors"
	"github.com/spf13/cobra"
	"github.com/vmware-tanzu-labs/educates-training-platform/client-programs/pkg/cluster"
	k8serrors "k8s.io/apimachinery/pkg/api/errors"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/apis/meta/v1/unstructured"
)

type WorkshopsListOptions struct {
	Kubeconfig string
	Portal     string
}

func (o *WorkshopsListOptions) Run() error {
	var err error

	// Ensure have portal name.

	if o.Portal == "" {
		o.Portal = "educates-cli"
	}

	clusterConfig := cluster.NewClusterConfig(o.Kubeconfig)

	dynamicClient, err := clusterConfig.GetDynamicClient()

	if err != nil {
		return errors.Wrapf(err, "unable to create Kubernetes client")
	}

	trainingPortalClient := dynamicClient.Resource(trainingPortalResource)

	trainingPortal, err := trainingPortalClient.Get(context.TODO(), o.Portal, metav1.GetOptions{})

	if k8serrors.IsNotFound(err) {
		fmt.Println("No workshops found.")
		return nil
	}

	sessionsMaximum, sessionsMaximumExists, err := unstructured.NestedInt64(trainingPortal.Object, "spec", "portal", "sessions", "maximum")

	workshops, _, err := unstructured.NestedSlice(trainingPortal.Object, "spec", "workshops")

	if err != nil {
		return errors.Wrap(err, "unable to retrieve workshops from training portal")
	}

	if len(workshops) == 0 {
		fmt.Println("No workshops found.")
		return nil
	}

	w := new(tabwriter.Writer)
	w.Init(os.Stdout, 8, 8, 3, ' ', 0)

	defer w.Flush()

	fmt.Fprintf(w, "%s\t%s\t%s\n", "NAME", "CAPACITY", "SOURCE")

	workshopsClient := dynamicClient.Resource(workshopResource)

	for _, item := range workshops {
		object := item.(map[string]interface{})
		name := object["name"].(string)

		var capacityField string

		capacity, capacityExists := object["capacity"]

		if capacityExists {
			capacityField = fmt.Sprintf("%d", capacity)
		} else if sessionsMaximumExists {
			capacityField = fmt.Sprintf("%d", sessionsMaximum)
		}

		workshop, err := workshopsClient.Get(context.TODO(), name, metav1.GetOptions{})

		source := ""

		if err == nil {
			annotations := workshop.GetAnnotations()

			if val, ok := annotations["training.educates.dev/source"]; ok {
				source = val
			}
		}

		fmt.Fprintf(w, "%s\t%s\t%s\n", object["name"], capacityField, source)
	}

	return nil
}

func (p *ProjectInfo) NewKubernetesWorkshopsListCmd() *cobra.Command {
	var o WorkshopsListOptions

	var c = &cobra.Command{
		Args:  cobra.NoArgs,
		Use:   "list-workshops",
		Short: "Output list of workshops",
		RunE:  func(_ *cobra.Command, _ []string) error { return o.Run() },
	}

	c.Flags().StringVar(
		&o.Kubeconfig,
		"kubeconfig",
		"",
		"kubeconfig file to use instead of $KUBECONFIG or $HOME/.kube/config",
	)
	c.Flags().StringVarP(
		&o.Portal,
		"portal",
		"p",
		"educates-cli",
		"name to be used for training portal and workshop name prefixes",
	)

	return c
}
