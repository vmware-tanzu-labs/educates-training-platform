/*
Copyright © 2022 The Educates Authors.
*/
package cmd

import (
	"context"
	"fmt"

	"github.com/pkg/errors"
	"github.com/spf13/cobra"
	"github.com/vmware-tanzu-labs/educates-training-platform/client-programs/educates/pkg/cluster"
	k8serrors "k8s.io/apimachinery/pkg/api/errors"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/apis/meta/v1/unstructured"
)

type WorkshopsCredentialsOptions struct {
	Kubeconfig string
	Admin      bool
}

func (o *WorkshopsCredentialsOptions) Run() error {
	var err error

	clusterConfig := cluster.NewClusterConfig(o.Kubeconfig)

	dynamicClient, err := clusterConfig.GetDynamicClient()

	if err != nil {
		return errors.Wrapf(err, "unable to create Kubernetes client")
	}

	trainingPortalClient := dynamicClient.Resource(trainingPortalResource)

	trainingPortal, err := trainingPortalClient.Get(context.TODO(), "educates-cli", metav1.GetOptions{})

	if k8serrors.IsNotFound(err) {
		return errors.New("no workshops deployed")
	}

	if o.Admin {
		username, found, err := unstructured.NestedString(trainingPortal.Object, "status", "educates", "credentials", "admin", "username")

		if err != nil || !found {
			return errors.New("unable to access credentials")
		}

		password, found, err := unstructured.NestedString(trainingPortal.Object, "status", "educates", "credentials", "admin", "password")

		if err != nil || !found {
			return errors.New("unable to access credentials")
		}

		fmt.Println("Username:", username)
		fmt.Println("Password:", password)
	} else {
		password, _, _ := unstructured.NestedString(trainingPortal.Object, "spec", "portal", "password")

		fmt.Println("Password:", password)
	}

	return nil
}

func NewWorkshopsCredentialsCmd() *cobra.Command {
	var o WorkshopsCredentialsOptions

	var c = &cobra.Command{
		Args:  cobra.NoArgs,
		Use:   "view-credentials",
		Short: "View credentials for workshops",
		RunE:  func(_ *cobra.Command, _ []string) error { return o.Run() },
	}

	c.Flags().StringVar(
		&o.Kubeconfig,
		"kubeconfig",
		"",
		"kubeconfig file to use instead of $KUBECONFIG or $HOME/.kube/config",
	)
	c.Flags().BoolVar(
		&o.Admin,
		"admin",
		false,
		"open URL for admin login instead of workshops catalog",
	)

	return c
}
