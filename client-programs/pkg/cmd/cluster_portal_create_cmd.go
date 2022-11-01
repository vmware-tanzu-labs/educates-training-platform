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

type ClusterConfigViewOptions struct {
	Kubeconfig string
	Portal     string
	Capacity   uint
	Password   string
}

func (o *ClusterConfigViewOptions) Run(isPasswordSet bool) error {
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

	// Update the training portal, creating it if necessary.

	err = createTrainingPortal(dynamicClient, o.Portal, o.Capacity, o.Password, isPasswordSet)

	if err != nil {
		return err
	}

	return nil
}

func (p *ProjectInfo) NewClusterPortalCreateCmd() *cobra.Command {
	var o ClusterConfigViewOptions

	var c = &cobra.Command{
		Args:  cobra.NoArgs,
		Use:   "create",
		Short: "Create portal in Kubernetes",
		RunE: func(cmd *cobra.Command, _ []string) error {
			isPasswordSet := cmd.Flags().Lookup("password").Changed

			return o.Run(isPasswordSet)
		},
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
	c.Flags().UintVar(
		&o.Capacity,
		"capacity",
		1,
		"maximum number of current sessions for the training portal",
	)
	c.Flags().StringVar(
		&o.Password,
		"password",
		"",
		"override password for training portal access",
	)

	return c
}

func createTrainingPortal(client dynamic.Interface, portal string, capacity uint, password string, isPasswordSet bool) error {
	trainingPortalClient := client.Resource(trainingPortalResource)

	trainingPortal, err := trainingPortalClient.Get(context.TODO(), portal, metav1.GetOptions{})

	if err != nil {
		if !k8serrors.IsNotFound(err) {
			return errors.Wrap(err, "unable to query training portal")
		}
	} else {
		return errors.New("training portal already exists")
	}

	trainingPortal = &unstructured.Unstructured{}

	if !isPasswordSet {
		password = randomPassword(12)
	}

	trainingPortal.SetUnstructuredContent(map[string]interface{}{
		"apiVersion": "training.educates.dev/v1beta1",
		"kind":       "TrainingPortal",
		"metadata": map[string]interface{}{
			"name": portal,
		},
		"spec": map[string]interface{}{
			"portal": map[string]interface{}{
				"password": password,
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
					Maximum int64 `json:"maximum"`
				}{
					Maximum: int64(capacity),
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

	_, err = trainingPortalClient.Create(context.TODO(), trainingPortal, metav1.CreateOptions{FieldManager: "educates-cli"})

	if err != nil {
		return errors.Wrapf(err, "unable to create training portal %q in cluster", portal)
	}

	return nil
}
