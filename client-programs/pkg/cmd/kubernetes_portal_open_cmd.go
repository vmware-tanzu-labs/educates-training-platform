// Copyright 2022 The Educates Authors.

package cmd

import (
	"context"
	"fmt"
	"os/exec"
	"runtime"

	"github.com/pkg/errors"
	"github.com/spf13/cobra"
	"github.com/vmware-tanzu-labs/educates-training-platform/client-programs/pkg/cluster"
	k8serrors "k8s.io/apimachinery/pkg/api/errors"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/apis/meta/v1/unstructured"
)

type PortalOpenOptions struct {
	Kubeconfig string
	Admin      bool
	Portal     string
}

func (o *PortalOpenOptions) Run() error {
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

	url, found, err := unstructured.NestedString(trainingPortal.Object, "status", "educates", "url")

	if !found {
		return errors.New("workshops not available")
	}

	if o.Admin {
		url = url + "/admin"
	}

	switch runtime.GOOS {
	case "linux":
		err = exec.Command("xdg-open", url).Start()
	case "windows":
		err = exec.Command("rundll32", "url.dll,FileProtocolHandler", url).Start()
	case "darwin":
		err = exec.Command("open", url).Start()
	default:
		err = fmt.Errorf("unsupported platform")
	}

	return err
}

func (p *ProjectInfo) NewKubernetesPortalOpenCmd() *cobra.Command {
	var o PortalOpenOptions

	var c = &cobra.Command{
		Args:  cobra.NoArgs,
		Use:   "open-portal",
		Short: "Open portal in web browser",
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
	c.Flags().StringVarP(
		&o.Portal,
		"portal",
		"p",
		"educates-cli",
		"name to be used for training portal and workshop name prefixes",
	)

	return c
}
