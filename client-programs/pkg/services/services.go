// Copyright 2022 The Educates Authors.

package services

import (
	"context"
	"fmt"
	"time"

	"github.com/pkg/errors"
	"gopkg.in/yaml.v2"
	apiv1 "k8s.io/api/core/v1"
	rbacv1 "k8s.io/api/rbac/v1"
	k8serrors "k8s.io/apimachinery/pkg/api/errors"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/apis/meta/v1/unstructured"
	"k8s.io/apimachinery/pkg/runtime/schema"
	"k8s.io/apimachinery/pkg/util/wait"
	"k8s.io/apimachinery/pkg/watch"

	"github.com/vmware-tanzu-labs/educates-training-platform/client-programs/pkg/cluster"
	"github.com/vmware-tanzu-labs/educates-training-platform/client-programs/pkg/config"
)

var kappAppResource = schema.GroupVersionResource{Group: "kappctrl.k14s.io", Version: "v1alpha1", Resource: "apps"}

func DeployServices(version string, clusterConfig *cluster.ClusterConfig, servicesConfig *config.ClusterEssentialsConfig) error {
	fmt.Println("Deploying cluster services ...")

	client, err := clusterConfig.GetClient()

	if err != nil {
		return err
	}

	serviceConfigData, err := yaml.Marshal(servicesConfig)

	if err != nil {
		return errors.Wrap(err, "failed to generate service config")
	}

	namespacesClient := client.CoreV1().Namespaces()

	_, err = namespacesClient.Get(context.TODO(), "educates-package", metav1.GetOptions{})

	if k8serrors.IsNotFound(err) {
		namespaceObj := apiv1.Namespace{
			ObjectMeta: metav1.ObjectMeta{
				Name: "educates-package",
			},
		}

		_, err = namespacesClient.Create(context.TODO(), &namespaceObj, metav1.CreateOptions{})
	}

	secretsClient := client.CoreV1().Secrets("educates-package")

	secret := &apiv1.Secret{
		ObjectMeta: metav1.ObjectMeta{
			Name: "educates-cluster-essentials-values",
		},
		Data: map[string][]byte{
			"values.yml": serviceConfigData,
		},
	}

	_, err = secretsClient.Create(context.TODO(), secret, metav1.CreateOptions{})

	if err != nil {
		return errors.Wrap(err, "unable to create services config secret")
	}

	serviceAccountsClient := client.CoreV1().ServiceAccounts("educates-package")

	serviceAccount := &apiv1.ServiceAccount{
		ObjectMeta: metav1.ObjectMeta{
			Name: "educates-cluster-essentials-deploy",
		},
	}

	_, err = serviceAccountsClient.Create(context.TODO(), serviceAccount, metav1.CreateOptions{})

	if err != nil {
		return errors.Wrap(err, "unable to create services service account")
	}

	clusterRoleBindingClient := client.RbacV1().ClusterRoleBindings()

	clusterRoleBinding := &rbacv1.ClusterRoleBinding{
		ObjectMeta: metav1.ObjectMeta{
			Name: "educates-cluster-essentials-deploy",
		},
		RoleRef: rbacv1.RoleRef{
			APIGroup: "rbac.authorization.k8s.io",
			Kind:     "ClusterRole",
			Name:     "cluster-admin",
		},
		Subjects: []rbacv1.Subject{
			{
				Kind:      "ServiceAccount",
				Name:      "educates-cluster-essentials-deploy",
				Namespace: "educates-package",
			},
		},
	}

	_, err = clusterRoleBindingClient.Create(context.TODO(), clusterRoleBinding, metav1.CreateOptions{})

	if err != nil {
		return errors.Wrap(err, "unable to create services role binding")
	}

	appResource := &unstructured.Unstructured{}
	appResource.SetUnstructuredContent(map[string]interface{}{
		"apiVersion": "kappctrl.k14s.io/v1alpha1",
		"kind":       "App",
		"metadata": map[string]interface{}{
			"name":      "educates-cluster-essentials",
			"namespace": "educates-package",
			"labels": map[string]string{
				"training.educates.dev/package": "cluster-essentials",
			},
		},
		"spec": map[string]interface{}{
			"serviceAccountName": "educates-cluster-essentials-deploy",
			"syncPeriod":         "1h",
			"fetch": []map[string]interface{}{
				{
					"imgpkgBundle": map[string]interface{}{
						"image": "ghcr.io/vmware-tanzu-labs/educates-cluster-essentials:" + version,
					},
				},
			},
			"template": []map[string]interface{}{
				{
					"ytt": map[string]interface{}{
						"paths": []string{
							"config",
						},
						"valuesFrom": []map[string]interface{}{
							{
								"secretRef": map[string]interface{}{
									"name": "educates-cluster-essentials-values",
								},
							},
						},
					},
				},
				{
					"kbld": map[string]interface{}{
						"paths": []string{
							".imgpkg/images.yml",
							"-",
						},
					},
				},
			},
			"deploy": []map[string]interface{}{
				{
					"kapp": map[string]interface{}{
						"rawOptions": []string{
							"--app-changes-max-to-keep=5",
						},
					},
				},
			},
		},
	})

	dynamicClient, err := clusterConfig.GetDynamicClient()

	if err != nil {
		return err
	}

	appResourceClient := dynamicClient.Resource(kappAppResource).Namespace("educates-package")

	_, err = appResourceClient.Create(context.TODO(), appResource, metav1.CreateOptions{})

	if err != nil {
		return errors.Wrap(err, "unable to create services app resource")
	}

	if err := wait.Poll(time.Duration(1)*time.Second, time.Duration(10)*time.Minute, func() (done bool, err error) {
		resource, err := appResourceClient.Get(context.TODO(), "educates-cluster-essentials", metav1.GetOptions{})

		if err != nil {
			return false, err
		}

		observedGeneration, exists, err := unstructured.NestedInt64(resource.Object, "status", "observedGeneration")

		if err != nil || !exists || resource.GetGeneration() != observedGeneration {
			return false, err
		}

		conditions, exists, err := unstructured.NestedSlice(resource.Object, "status", "conditions")

		if !exists {
			return false, err
		}

		statusUsefulErrorMessage, _, _ := unstructured.NestedString(resource.Object, "status.usefulErrorMessage")
		statusFriendlyDescription, _, _ := unstructured.NestedString(resource.Object, "status.friendlyDescription")

		for _, condition := range conditions {
			conditionObject := condition.(map[string]interface{})

			conditionType, _, _ := unstructured.NestedString(conditionObject, "type")
			conditionStatus, _, _ := unstructured.NestedString(conditionObject, "status")

			switch {
			case conditionType == "ReconcileSucceeded" && conditionStatus == string(apiv1.ConditionTrue):
				return true, nil
			case conditionType == "ReconcileFailed" && conditionStatus == string(apiv1.ConditionTrue):
				return false, fmt.Errorf("%s. %s", statusUsefulErrorMessage, statusFriendlyDescription)
			}
		}
		return false, nil
	}); err != nil {
		return fmt.Errorf("%s: Reconciling: educates-package/educates-cluster-essentials", err)
	}

	return nil
}

func DeleteServices(clusterConfig *cluster.ClusterConfig, servicesConfig *config.ClusterEssentialsConfig) error {
	dynamicClient, err := clusterConfig.GetDynamicClient()

	if err != nil {
		return err
	}

	appResourceClient := dynamicClient.Resource(kappAppResource).Namespace("educates-package")

	err = appResourceClient.Delete(context.TODO(), "educates-cluster-essentials", metav1.DeleteOptions{})

	if err == nil {
		timeout := int64(300)

		watcher, err := appResourceClient.Watch(context.TODO(), metav1.ListOptions{
			LabelSelector:  "training.educates.dev/package=cluster-essentials",
			TimeoutSeconds: &timeout,
		})

		if err != nil {
			return err
		}

		defer watcher.Stop()

	watch:
		for {
			select {
			case event := <-watcher.ResultChan():
				if event.Type == watch.Deleted {
					break watch
				}
			case <-context.TODO().Done():
				return errors.New("timeout waiting for service deletion")
			}
		}
	} else {
		// return err
	}

	client, err := clusterConfig.GetClient()

	if err != nil {
		return err
	}

	clusterRoleBindingClient := client.RbacV1().ClusterRoleBindings()

	err = clusterRoleBindingClient.Delete(context.TODO(), "educates-cluster-essentials-deploy", metav1.DeleteOptions{})

	// if err != nil {
	// 	return err
	// }

	serviceAccountsClient := client.CoreV1().ServiceAccounts("educates-package")

	err = serviceAccountsClient.Delete(context.TODO(), "educates-cluster-essentials-deploy", metav1.DeleteOptions{})

	// if err != nil {
	// 	return err
	// }

	secretsClient := client.CoreV1().Secrets("educates-package")

	err = secretsClient.Delete(context.TODO(), "educates-cluster-essentials-values", metav1.DeleteOptions{})

	// if err != nil {
	// 	return err
	// }

	return nil
}
