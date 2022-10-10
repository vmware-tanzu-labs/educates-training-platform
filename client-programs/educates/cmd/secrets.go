/*
Copyright © 2022 The Educates Authors.
*/
package cmd

import (
	"context"
	"io/ioutil"
	"os"
	"path"
	"strings"

	"github.com/adrg/xdg"
	"github.com/pkg/errors"
	"github.com/spf13/cobra"
	apiv1 "k8s.io/api/core/v1"
	k8serrors "k8s.io/apimachinery/pkg/api/errors"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/runtime"
	"k8s.io/apimachinery/pkg/runtime/serializer"
	applycorev1 "k8s.io/client-go/applyconfigurations/core/v1"
	"k8s.io/client-go/kubernetes"
	"k8s.io/kubectl/pkg/scheme"
)

func NewSecretsCmd() *cobra.Command {
	var secretsCmd = &cobra.Command{
		Use:   "cluster-secrets",
		Short: "Manage local secrets cache",
	}

	secretsCmd.AddCommand(
		NewSecretsAddCmd(),
		NewSecretsExportCmd(),
		NewSecretsListCmd(),
		NewSecretsRemoveCmd(),
		NewSecretsSyncCmd(),
	)

	return secretsCmd
}

func CachedSecretForDomain(domain string) string {
	configFileDir := path.Join(xdg.DataHome, "educates")
	secretsCacheDir := path.Join(configFileDir, "secrets")

	files, err := ioutil.ReadDir(secretsCacheDir)

	if err != nil {
		return ""
	}

	for _, f := range files {
		if strings.HasSuffix(f.Name(), ".yaml") {
			name := strings.TrimSuffix(f.Name(), ".yaml")
			fullPath := path.Join(secretsCacheDir, f.Name())

			yamlData, err := os.ReadFile(fullPath)

			if err != nil {
				continue
			}

			decoder := serializer.NewCodecFactory(scheme.Scheme).UniversalDecoder()
			secretObj := &apiv1.Secret{}
			err = runtime.DecodeInto(decoder, yamlData, secretObj)

			if err != nil {
				return ""
			}

			annotations := secretObj.ObjectMeta.Annotations

			var val string
			var found bool

			if val, found = annotations["training.educates.dev/domain"]; !found {
				return ""
			}

			if val != domain {
				return ""
			}

			return name
		}
	}

	return ""
}

func SyncSecretsToCluster(client *kubernetes.Clientset) error {
	configFileDir := path.Join(xdg.DataHome, "educates")
	secretsCacheDir := path.Join(configFileDir, "secrets")

	err := os.MkdirAll(secretsCacheDir, os.ModePerm)

	if err != nil {
		return errors.Wrapf(err, "unable to create secrets cache directory")
	}

	namespacesClient := client.CoreV1().Namespaces()

	_, err = namespacesClient.Get(context.TODO(), "educates-secrets", metav1.GetOptions{})

	if k8serrors.IsNotFound(err) {
		namespaceObj := apiv1.Namespace{
			ObjectMeta: metav1.ObjectMeta{
				Name: "educates-secrets",
			},
		}

		_, err = namespacesClient.Create(context.TODO(), &namespaceObj, metav1.CreateOptions{})
	}

	secretsClient := client.CoreV1().Secrets("educates-secrets")

	files, err := ioutil.ReadDir(secretsCacheDir)

	if err != nil {
		return errors.Wrapf(err, "unable to read secrets cache directory %q", secretsCacheDir)
	}

	for _, f := range files {
		if strings.HasSuffix(f.Name(), ".yaml") {
			name := strings.TrimSuffix(f.Name(), ".yaml")
			fullPath := path.Join(secretsCacheDir, f.Name())

			yamlData, err := os.ReadFile(fullPath)

			if err != nil {
				continue
			}

			decoder := serializer.NewCodecFactory(scheme.Scheme).UniversalDecoder()
			secretObj := &apiv1.Secret{}
			err = runtime.DecodeInto(decoder, yamlData, secretObj)

			if err != nil {
				return errors.Wrapf(err, "unable to read secret file %q", fullPath)
			}

			_, err = secretsClient.Get(context.TODO(), name, metav1.GetOptions{})

			if err != nil {
				if !k8serrors.IsNotFound(err) {
					return errors.Wrap(err, "unable to read secrets from cluster")
				} else {
					_, err = secretsClient.Create(context.TODO(), secretObj, metav1.CreateOptions{})

					if err != nil {
						return errors.Wrapf(err, "unable to copy secret to cluster %q", name)
					}
				}
			} else {
				patch := applycorev1.Secret(name, "educates-secrets").WithType(secretObj.Type).WithData(secretObj.Data)

				_, err = secretsClient.Apply(context.TODO(), patch, metav1.ApplyOptions{FieldManager: "kubectl-create", Force: true})

				if err != nil {
					return errors.Wrapf(err, "unable to update secret in cluster %q", name)
				}
			}
		}
	}

	return nil
}
