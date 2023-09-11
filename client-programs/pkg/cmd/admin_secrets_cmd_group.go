package cmd

import (
	"context"
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
	"k8s.io/kubectl/pkg/util/templates"
)

func (p *ProjectInfo) NewAdminSecretsCmdGroup() *cobra.Command {
	var c = &cobra.Command{
		Use:   "secrets",
		Short: "Manage local secrets cache",
	}

	// Use a command group as it allows us to dictate the order in which they
	// are displayed in the help message, as otherwise they are displayed in
	// sort order.

	commandGroups := templates.CommandGroups{
		{
			Message: "Available Commands:",
			Commands: []*cobra.Command{
				p.NewAdminSecretsAddCmdGroup(),
				p.NewAdminSecretsListCmd(),
				p.NewAdminSecretsExportCmd(),
				p.NewAdminSecretsImportCmd(),
				p.NewAdminSecretsSyncCmd(),
				p.NewAdminSecretsRemoveCmd(),
			},
		},
	}

	commandGroups.Add(c)

	templates.ActsAsRootCommand(c, []string{"--help"}, commandGroups...)

	return c
}

func CachedSecretForIngressDomain(domain string) string {
	configFileDir := path.Join(xdg.DataHome, "educates")
	secretsCacheDir := path.Join(configFileDir, "secrets")

	files, err := os.ReadDir(secretsCacheDir)

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
				continue
			}

			annotations := secretObj.ObjectMeta.Annotations

			var val string
			var found bool

			// Domain name must match.

			if val, found = annotations["training.educates.dev/domain"]; !found {
				continue
			}

			if val != domain {
				continue
			}

			// Type of secret needs to be kubernetes.io/tls.

			if secretObj.Type != "kubernetes.io/tls" {
				continue
			}

			// Needs contain tls.crt and tls.key data.

			if value, exists := secretObj.Data["tls.crt"]; !exists || len(value) == 0 {
				continue
			}

			if value, exists := secretObj.Data["tls.key"]; !exists || len(value) == 0 {
				continue
			}

			return name
		}
	}

	return ""
}

func CachedSecretForCertificateAuthority(domain string) string {
	configFileDir := path.Join(xdg.DataHome, "educates")
	secretsCacheDir := path.Join(configFileDir, "secrets")

	files, err := os.ReadDir(secretsCacheDir)

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
				continue
			}

			annotations := secretObj.ObjectMeta.Annotations

			var val string
			var found bool

			// Domain name must match.

			if val, found = annotations["training.educates.dev/domain"]; !found {
				continue
			}

			if val != domain {
				continue
			}

			// Type of secret needs to be Opaque.

			if secretObj.Type != "Opaque" && secretObj.Type != "" {
				continue
			}

			// Needs contain ca.crt data.

			if value, exists := secretObj.Data["ca.crt"]; !exists || len(value) == 0 {
				continue
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

		namespacesClient.Create(context.TODO(), &namespaceObj, metav1.CreateOptions{})
	}

	secretsClient := client.CoreV1().Secrets("educates-secrets")

	files, err := os.ReadDir(secretsCacheDir)

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

			secretObj.ObjectMeta.Namespace = ""

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
				var patch *applycorev1.SecretApplyConfiguration

				if len(secretObj.StringData) != 0 {
					patch = applycorev1.Secret(name, "educates-secrets").WithType(secretObj.Type).WithStringData(secretObj.StringData)
				} else {
					patch = applycorev1.Secret(name, "educates-secrets").WithType(secretObj.Type).WithData(secretObj.Data)
				}

				_, err = secretsClient.Apply(context.TODO(), patch, metav1.ApplyOptions{FieldManager: "educates-cli", Force: true})

				if err != nil {
					return errors.Wrapf(err, "unable to update secret in cluster %q", name)
				}
			}
		}
	}

	return nil
}
