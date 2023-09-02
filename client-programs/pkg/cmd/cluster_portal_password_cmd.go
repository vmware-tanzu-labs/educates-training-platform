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

type ClusterPortalPasswordOptions struct {
	Kubeconfig string
	Admin      bool
	Portal     string
}

func (o *ClusterPortalPasswordOptions) Run() error {
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

		w := new(tabwriter.Writer)
		w.Init(os.Stdout, 8, 8, 3, ' ', 0)

		defer w.Flush()

		fmt.Fprintf(w, "%s\t%s\n", "USERNAME", "PASSWORD")
		fmt.Fprintf(w, "%s\t%s\n", username, password)
	} else {
		password, _, _ := unstructured.NestedString(trainingPortal.Object, "spec", "portal", "password")

		fmt.Println(password)
	}

	return nil
}

func (p *ProjectInfo) NewClusterPortalPasswordCmd() *cobra.Command {
	var o ClusterPortalPasswordOptions

	var c = &cobra.Command{
		Args:  cobra.NoArgs,
		Use:   "password",
		Short: "View credentials for training portal",
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
		"view admin password for admin pages rather than access code",
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
