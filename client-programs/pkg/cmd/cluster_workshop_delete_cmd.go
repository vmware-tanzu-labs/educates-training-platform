// Copyright 2022 The Educates Authors.

package cmd

import (
	"context"

	"github.com/pkg/errors"
	"github.com/spf13/cobra"
	"github.com/vmware-tanzu-labs/educates-training-platform/client-programs/pkg/cluster"
	k8serrors "k8s.io/apimachinery/pkg/api/errors"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/apis/meta/v1/unstructured"
	"k8s.io/client-go/dynamic"
)

type ClusterWorkshopDeleteOptions struct {
	Name       string
	Path       string
	Kubeconfig string
	Portal     string
}

func (o *ClusterWorkshopDeleteOptions) Run() error {
	var err error

	var name = o.Name

	// Ensure have portal name.

	if o.Portal == "" {
		o.Portal = "educates-cli"
	}

	if name == "" {
		var path = o.Path

		// If path not provided assume the current working directory. When loading
		// the workshop will then expect the workshop definition to reside in the
		// resources/workshop.yaml file under the directory, the same as if a
		// directory path was provided explicitly.

		if path == "" {
			path = "."
		}

		// Load the workshop definition. The path can be a HTTP/HTTPS URL for a
		// local file system path for a directory or file.

		var workshop *unstructured.Unstructured

		if workshop, err = loadWorkshopDefinition(o.Name, path, o.Portal); err != nil {
			return err
		}

		name = workshop.GetName()
	}

	clusterConfig := cluster.NewClusterConfig(o.Kubeconfig)

	dynamicClient, err := clusterConfig.GetDynamicClient()

	if err != nil {
		return errors.Wrapf(err, "unable to create Kubernetes client")
	}

	// Delete the deployed workshop from the Kubernetes cluster.

	err = deleteWorkshopResource(dynamicClient, name, o.Portal)

	if err != nil {
		return err
	}

	return nil
}

func (p *ProjectInfo) NewClusterWorkshopDeleteCmd() *cobra.Command {
	var o ClusterWorkshopDeleteOptions

	var c = &cobra.Command{
		Args:  cobra.NoArgs,
		Use:   "delete",
		Short: "Delete workshop from Kubernetes",
		RunE:  func(_ *cobra.Command, _ []string) error { return o.Run() },
	}

	c.Flags().StringVarP(
		&o.Name,
		"name",
		"n",
		"",
		"name to be used for the workshop definition, generated if not set",
	)
	c.Flags().StringVarP(
		&o.Path,
		"file",
		"f",
		".",
		"path to local workshop directory, definition file, or URL for workshop definition file",
	)
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

func deleteWorkshopResource(client dynamic.Interface, name string, portal string) error {
	trainingPortalClient := client.Resource(trainingPortalResource)

	trainingPortal, err := trainingPortalClient.Get(context.TODO(), portal, metav1.GetOptions{})

	if k8serrors.IsNotFound(err) {
		return nil
	}

	workshops, _, err := unstructured.NestedSlice(trainingPortal.Object, "spec", "workshops")

	if err != nil {
		return errors.Wrap(err, "unable to retrieve workshops from training portal")
	}

	var found = false

	var updatedWorkshops []interface{}

	for _, item := range workshops {
		object := item.(map[string]interface{})

		if object["name"] != name {
			updatedWorkshops = append(updatedWorkshops, object)
		} else {
			found = true
		}
	}

	if !found {
		return nil
	}

	unstructured.SetNestedSlice(trainingPortal.Object, updatedWorkshops, "spec", "workshops")

	_, err = trainingPortalClient.Update(context.TODO(), trainingPortal, metav1.UpdateOptions{FieldManager: "educates-cli"})

	if err != nil {
		return errors.Wrapf(err, "unable to update training portal %q in cluster", portal)
	}

	return nil
}
