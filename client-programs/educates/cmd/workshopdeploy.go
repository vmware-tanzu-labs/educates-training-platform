/*
Copyright © 2022 The Educates Authors.
*/
package cmd

import (
	"context"
	"math/rand"
	"strings"
	"time"

	"github.com/pkg/errors"
	"github.com/spf13/cobra"
	"github.com/vmware-tanzu-labs/educates-training-platform/client-programs/educates/pkg/cluster"
	k8serrors "k8s.io/apimachinery/pkg/api/errors"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/apis/meta/v1/unstructured"
	"k8s.io/apimachinery/pkg/runtime/schema"
	"k8s.io/client-go/dynamic"
)

type WorkshopDeployOptions struct {
	Name       string
	Path       string
	Kubeconfig string
	Portal     string
}

func (o *WorkshopDeployOptions) Run() error {
	var err error

	var path = o.Path

	// Ensure have portal name.

	if o.Portal == "" {
		o.Portal = "educates-cli"
	}

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

	clusterConfig := cluster.NewClusterConfig(o.Kubeconfig)

	dynamicClient, err := clusterConfig.GetDynamicClient()

	if err != nil {
		return errors.Wrapf(err, "unable to create Kubernetes client")
	}

	// Update the workshop resource in the Kubernetes cluster.

	err = updateWorkshopResource(dynamicClient, workshop)

	if err != nil {
		return err
	}

	// Update the training portal, creating it if necessary.

	err = deployWorkshopResource(dynamicClient, workshop, o.Portal)

	if err != nil {
		return err
	}

	return nil
}

func NewWorkshopDeployCmd() *cobra.Command {
	var o WorkshopDeployOptions

	var c = &cobra.Command{
		Args:  cobra.NoArgs,
		Use:   "deploy-workshop",
		Short: "Deploy workshop to Kubernetes",
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

var trainingPortalResource = schema.GroupVersionResource{Group: "training.educates.dev", Version: "v1beta1", Resource: "trainingportals"}

func deployWorkshopResource(client dynamic.Interface, workshop *unstructured.Unstructured, portal string) error {
	trainingPortalClient := client.Resource(trainingPortalResource)

	trainingPortal, err := trainingPortalClient.Get(context.TODO(), portal, metav1.GetOptions{})

	var trainingPortalExists = true

	if k8serrors.IsNotFound(err) {
		trainingPortalExists = false

		trainingPortal = &unstructured.Unstructured{}

		trainingPortal.SetUnstructuredContent(map[string]interface{}{
			"apiVersion": "training.educates.dev/v1beta1",
			"kind":       "TrainingPortal",
			"metadata": map[string]interface{}{
				"name": portal,
			},
			"spec": map[string]interface{}{
				"portal": map[string]interface{}{
					"password": randomPassword(12),
					"registration": struct {
						Type string `json:"type"`
					}{
						Type: "anonymous",
					},
					"updates": struct {
						Workshop bool `json:"workshop"`
					}{
						Workshop: true,
					},
					"sessions": struct {
						Maximum int `json:"maximum"`
					}{
						Maximum: 1,
					},
					"workshop": map[string]interface{}{
						"defaults": struct {
							Reserved int `json:"reserved"`
						}{
							Reserved: 0,
						},
					},
				},
				"workshops": []interface{}{},
			},
		})
	}

	workshops, _, err := unstructured.NestedSlice(trainingPortal.Object, "spec", "workshops")

	if err != nil {
		return errors.Wrap(err, "unable to retrieve workshops from training portal")
	}

	var found = false

	var updatedWorkshops []interface{}

	for _, item := range workshops {
		object := item.(map[string]interface{})

		updatedWorkshops = append(updatedWorkshops, object)

		if object["name"] == workshop.GetName() {
			found = true
		}
	}

	if !found {
		expires, exists, err := unstructured.NestedString(workshop.Object, "spec", "duration")

		if err != nil || !exists {
			expires = "60m"
		}

		updatedWorkshops = append(updatedWorkshops, map[string]interface{}{
			"name":     workshop.GetName(),
			"expires":  expires,
			"orphaned": "15m",
		})
	}

	unstructured.SetNestedSlice(trainingPortal.Object, updatedWorkshops, "spec", "workshops")

	if trainingPortalExists {
		_, err = trainingPortalClient.Update(context.TODO(), trainingPortal, metav1.UpdateOptions{FieldManager: "educates-cli"})
	} else {
		_, err = trainingPortalClient.Create(context.TODO(), trainingPortal, metav1.CreateOptions{FieldManager: "educates-cli"})
	}

	if err != nil {
		return errors.Wrapf(err, "unable to update training portal %q in cluster", portal)
	}

	return nil
}

func randomPassword(length int) string {
	rand.Seed(time.Now().UnixNano())

	chars := []rune("!#%+23456789:=?@ABCDEFGHJKLMNPRSTUVWXYZabcdefghijkmnopqrstuvwxyz")

	var b strings.Builder

	for i := 0; i < length; i++ {
		b.WriteRune(chars[rand.Intn(len(chars))])
	}
	return b.String()
}
