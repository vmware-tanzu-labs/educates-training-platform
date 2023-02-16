// Copyright 2022-2023 The Educates Authors.

package cmd

import (
	"context"
	"fmt"

	"github.com/pkg/errors"
	"github.com/spf13/cobra"
	"github.com/vmware-tanzu-labs/educates-training-platform/client-programs/pkg/cluster"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/kubectl/pkg/util/templates"
)

func (p *ProjectInfo) NewAdminServicesConfigCmdGroup() *cobra.Command {
	var c = &cobra.Command{
		Use:   "config",
		Short: "Manage services configuration",
	}

	// Use a command group as it allows us to dictate the order in which they
	// are displayed in the help message, as otherwise they are displayed in
	// sort order.

	commandGroups := templates.CommandGroups{
		{
			Message: "Available Commands:",
			Commands: []*cobra.Command{
				p.NewAdminServicesConfigViewCmd(),
				// p.NewAdminServicesConfigUpdateCmd(),
			},
		},
	}

	commandGroups.Add(c)

	templates.ActsAsRootCommand(c, []string{"options"}, commandGroups...)

	return c
}

type AdminServicesConfigViewOptions struct {
	Kubeconfig string
}

func (o *AdminServicesConfigViewOptions) Run() error {
	clusterConfig := cluster.NewKindClusterConfig(o.Kubeconfig)

	client, err := clusterConfig.GetClient()

	if err != nil {
		return errors.Wrapf(err, "unable to create Kubernetes client")
	}

	secretsClient := client.CoreV1().Secrets("educates-package")

	valuesSecret, err := secretsClient.Get(context.TODO(), "educates-cluster-essentials-values", metav1.GetOptions{})

	if err != nil {
		return errors.Wrap(err, "platform not deployed")
	}

	valuesData, ok := valuesSecret.Data["values.yml"]

	if !ok {
		return errors.New("no platform configuration found")
	}

	fmt.Print(string(valuesData))

	return nil
}

func (p *ProjectInfo) NewAdminServicesConfigViewCmd() *cobra.Command {
	var o AdminServicesConfigViewOptions

	var c = &cobra.Command{
		Args:  cobra.NoArgs,
		Use:   "view",
		Short: "View services configuration",
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
