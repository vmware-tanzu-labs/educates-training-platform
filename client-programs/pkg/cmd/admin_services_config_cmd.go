package cmd

import (
	"context"
	"encoding/json"
	"fmt"

	"github.com/pkg/errors"
	"github.com/spf13/cobra"
	"github.com/vmware-tanzu-labs/educates-training-platform/client-programs/pkg/cluster"
	"github.com/vmware-tanzu-labs/educates-training-platform/client-programs/pkg/config"
	"gopkg.in/yaml.v2"
	apiv1 "k8s.io/api/core/v1"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/types"
	applycorev1 "k8s.io/client-go/applyconfigurations/core/v1"
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
				p.NewAdminServicesConfigUpdateCmd(),
			},
		},
	}

	commandGroups.Add(c)

	templates.ActsAsRootCommand(c, []string{"--help"}, commandGroups...)

	return c
}

type AdminServicesConfigViewOptions struct {
	Kubeconfig string
}

func (o *AdminServicesConfigViewOptions) Run() error {
	clusterConfig := cluster.NewClusterConfig(o.Kubeconfig)

	client, err := clusterConfig.GetClient()

	if err != nil {
		return errors.Wrapf(err, "unable to create Kubernetes client")
	}

	secretsClient := client.CoreV1().Secrets("educates-package")

	valuesSecret, err := secretsClient.Get(context.TODO(), "educates-cluster-essentials-values", metav1.GetOptions{})

	if err != nil {
		return errors.Wrap(err, "services not deployed")
	}

	valuesData, ok := valuesSecret.Data["values.yml"]

	if !ok {
		return errors.New("no services configuration found")
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

type AdminServicesConfigUpdateOptions struct {
	Config     string
	Reconcile  bool
	Kubeconfig string
}

func (o *AdminServicesConfigUpdateOptions) Run() error {
	clusterConfig := cluster.NewClusterConfig(o.Kubeconfig)

	client, err := clusterConfig.GetClient()

	if err != nil {
		return errors.Wrapf(err, "unable to create Kubernetes client")
	}

	secretsClient := client.CoreV1().Secrets("educates-package")

	valuesSecret, err := secretsClient.Get(context.TODO(), "educates-cluster-essentials-values", metav1.GetOptions{})

	if err != nil {
		return errors.Wrap(err, "services not deployed")
	}

	valuesData, ok := valuesSecret.Data["values.yml"]

	if !ok {
		return errors.New("no services configuration found")
	}

	fullConfig, err := config.NewInstallationConfigFromFile(o.Config)

	if err != nil {
		return err
	}

	var valuesObj config.ClusterEssentialsConfig

	err = yaml.Unmarshal(valuesData, &valuesObj)

	if err != nil {
		return errors.Wrap(err, "invalid services configuration")
	}

	fullConfig.ClusterInfrastructure = valuesObj.ClusterInfrastructure

	servicesConfig := config.ClusterEssentialsConfig{
		ClusterInfrastructure: fullConfig.ClusterInfrastructure,
		ClusterPackages:       fullConfig.ClusterPackages,
		ClusterSecurity:       fullConfig.ClusterSecurity,
	}

	servicesConfigData, err := yaml.Marshal(servicesConfig)

	if err != nil {
		return errors.Wrap(err, "failed to generate services configuration")
	}

	secretObj := &apiv1.Secret{
		Data: map[string][]byte{},
	}

	secretObj.Data["values.yml"] = servicesConfigData

	patch := applycorev1.Secret("educates-cluster-essentials-values", "educates-package").WithType(secretObj.Type).WithData(secretObj.Data)

	_, err = secretsClient.Apply(context.TODO(), patch, metav1.ApplyOptions{FieldManager: "educates-cli", Force: true})

	if err != nil {
		return errors.Wrapf(err, "unable to update services configuration")
	}

	if o.Reconcile {
		dynamicClient, err := clusterConfig.GetDynamicClient()

		if err != nil {
			return err
		}

		appResourceClient := dynamicClient.Resource(kappAppResource).Namespace("educates-package")

		pausePatch := []map[string]interface{}{
			{
				"op":    "add",
				"path":  "/spec/paused",
				"value": true,
			},
		}

		patchJSON, err := json.Marshal(pausePatch)

		if err != nil {
			return errors.Wrapf(err, "unable to create patch for deployment")
		}

		_, err = appResourceClient.Patch(context.TODO(), "educates-cluster-essentials", types.JSONPatchType, patchJSON, metav1.PatchOptions{})

		if err != nil {
			return errors.Wrapf(err, "unable to pause reconcilation")
		}

		unpausePatch := []map[string]interface{}{
			{
				"op":   "remove",
				"path": "/spec/paused",
			},
		}

		patchJSON, err = json.Marshal(unpausePatch)

		if err != nil {
			return errors.Wrapf(err, "unable to create patch for deployment")
		}

		_, err = appResourceClient.Patch(context.TODO(), "educates-cluster-essentials", types.JSONPatchType, patchJSON, metav1.PatchOptions{})

		if err != nil {
			return errors.Wrapf(err, "unable to resume reconcilation")
		}
	}

	return nil
}

func (p *ProjectInfo) NewAdminServicesConfigUpdateCmd() *cobra.Command {
	var o AdminServicesConfigUpdateOptions

	var c = &cobra.Command{
		Args:  cobra.NoArgs,
		Use:   "update",
		Short: "Update services configuration",
		RunE:  func(_ *cobra.Command, _ []string) error { return o.Run() },
	}

	c.Flags().StringVar(
		&o.Config,
		"config",
		"",
		"path to the installation config file for Educates",
	)
	c.Flags().BoolVar(
		&o.Reconcile,
		"reconcile",
		false,
		"trigger reconcilation after configuration update",
	)
	c.Flags().StringVar(
		&o.Kubeconfig,
		"kubeconfig",
		"",
		"kubeconfig file to use instead of $KUBECONFIG or $HOME/.kube/config",
	)

	return c
}
