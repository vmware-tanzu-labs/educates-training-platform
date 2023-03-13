// Copyright 2022-2023 The Educates Authors.

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

type ClusterPortalListOptions struct {
	Kubeconfig string
}

func (o *ClusterPortalListOptions) Run() error {
	var err error

	clusterConfig := cluster.NewClusterConfig(o.Kubeconfig)

	dynamicClient, err := clusterConfig.GetDynamicClient()

	if err != nil {
		return errors.Wrapf(err, "unable to create Kubernetes client")
	}

	trainingPortalClient := dynamicClient.Resource(trainingPortalResource)

	trainingPortals, err := trainingPortalClient.List(context.TODO(), metav1.ListOptions{})

	if k8serrors.IsNotFound(err) {
		fmt.Println("No portals found.")
		return nil
	}

	w := new(tabwriter.Writer)
	w.Init(os.Stdout, 8, 8, 3, ' ', 0)

	defer w.Flush()

	fmt.Fprintf(w, "%s\t%s\t%s\n", "NAME", "CAPACITY", "URL")

	for _, item := range trainingPortals.Items {
		name := item.GetName()

		sessionsMaximum, propertyExists, err := unstructured.NestedInt64(item.Object, "spec", "portal", "sessions", "maximum")

		var capacity string

		if err == nil && propertyExists {
			capacity = fmt.Sprintf("%d", sessionsMaximum)
		}

		url, _, _ := unstructured.NestedString(item.Object, "status", "educates", "url")

		fmt.Fprintf(w, "%s\t%s\t%s\n", name, capacity, url)
	}

	return nil
}

func (p *ProjectInfo) NewClusterPortalListCmd() *cobra.Command {
	var o ClusterPortalListOptions

	var c = &cobra.Command{
		Args:  cobra.NoArgs,
		Use:   "list",
		Short: "Output list of portals",
		RunE:  func(_ *cobra.Command, _ []string) error { return o.Run() },
	}

	c.Flags().StringVar(
		&o.Kubeconfig,
		"kubeconfig",
		"",
		"kubeconfig file to use instead of $KUBECONFIG or $HOME/.kube/config",
	)

	return c
}
