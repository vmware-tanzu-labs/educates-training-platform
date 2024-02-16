package dev

import (
	"fmt"

	"github.com/vmware-tanzu-labs/educates-training-platform/client-programs/pkg/config"
	kcv1alpha1 "github.com/vmware-tanzu/carvel-kapp-controller/pkg/apis/kappctrl/v1alpha1"
	yttyaml "gopkg.in/yaml.v2"
	corev1 "k8s.io/api/core/v1"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"sigs.k8s.io/yaml"
)

const EducatesInstallerString = "educates-installer"

type Deployments struct {
	App    kcv1alpha1.App
	Secret corev1.Secret
}

func NewDeploymentsForInstall(fullConfig *config.InstallationConfig, imageRef string, verbose bool) (Deployments, error) {
	var Deployments Deployments

	createApp(fullConfig, imageRef, &Deployments, verbose)
	createSecret(fullConfig, &Deployments, verbose)

	return Deployments, nil
}

func NewDeploymentsForDelete(fullConfig *config.InstallationConfig, verbose bool) (Deployments, error) {
	var Deployments Deployments

	createAppForDelete(fullConfig, &Deployments, verbose)

	return Deployments, nil
}

func createApp(fullConfig *config.InstallationConfig, imageRef string, Deployments *Deployments, verbose bool) error {
	Deployments.App = kcv1alpha1.App{
		TypeMeta: metav1.TypeMeta{
			Kind:       "App",
			APIVersion: "kappctrl.k14s.io/v1alpha1",
		},
		ObjectMeta: metav1.ObjectMeta{
			Name:      EducatesInstallerString,
			Namespace: EducatesInstallerString,
		},
		Spec: kcv1alpha1.AppSpec{
			ServiceAccountName: EducatesInstallerString,
			Fetch: []kcv1alpha1.AppFetch{
				{
					ImgpkgBundle: &kcv1alpha1.AppFetchImgpkgBundle{
						Image: imageRef,
					},
				},
			},
			Template: []kcv1alpha1.AppTemplate{
				{
					Ytt: &kcv1alpha1.AppTemplateYtt{
						Paths: []string{"config", "kbld/kbld-bundle.yaml"},
						ValuesFrom: []kcv1alpha1.AppTemplateValuesSource{
							{
								SecretRef: &kcv1alpha1.AppTemplateValuesSourceRef{
									Name: EducatesInstallerString,
								},
							},
							{
								Path: "kbld/kbld-images.yaml",
							},
						},
					},
				},
				{
					Kbld: &kcv1alpha1.AppTemplateKbld{
						Paths: []string{"-", ".imgpkg/images.yml"},
					},
				},
			},
			Deploy: []kcv1alpha1.AppDeploy{
				{
					Kapp: &kcv1alpha1.AppDeployKapp{
						RawOptions: []string{"--app-changes-max-to-keep=0", "--wait-timeout=10m"},
					},
				},
			},
		},
	}
	return nil
}

func createAppForDelete(fullConfig *config.InstallationConfig, Deployments *Deployments, verbose bool) error {
	Deployments.App = kcv1alpha1.App{
		TypeMeta: metav1.TypeMeta{
			Kind:       "App",
			APIVersion: "kappctrl.k14s.io/v1alpha1",
		},
		ObjectMeta: metav1.ObjectMeta{
			Name:      EducatesInstallerString,
			Namespace: EducatesInstallerString,
		},
		Spec: kcv1alpha1.AppSpec{
			ServiceAccountName: EducatesInstallerString,
			Deploy: []kcv1alpha1.AppDeploy{
				{
					Kapp: &kcv1alpha1.AppDeployKapp{
						RawOptions: []string{"--app-changes-max-to-keep=0", "--wait-timeout=10m"},
					},
				},
			},
		},
	}
	return nil
}

func createSecret(fullConfig *config.InstallationConfig, Deployments *Deployments, verbose bool) error {
	yamlBytes, err := yttyaml.Marshal(fullConfig)
	if err != nil {
		return err
	}
	if verbose {
		fmt.Println("Configuration:")
		fmt.Println("----------------------------")
		fmt.Println(string(yamlBytes))
		fmt.Println("----------------------------")
	}

	Deployments.Secret = corev1.Secret{
		TypeMeta: metav1.TypeMeta{
			Kind:       "Secret",
			APIVersion: "v1",
		},
		ObjectMeta: metav1.ObjectMeta{
			Name:      EducatesInstallerString,
			Namespace: EducatesInstallerString,
		},
		Data: map[string][]byte{
			// Insert yamlBytes as value in the below map
			"values.yaml": []byte(yamlBytes),
		},
	}
	return nil
}

func PrintApp(app *kcv1alpha1.App) {
	bs, err := yaml.Marshal(app)
	if err != nil {
		fmt.Errorf("Marshaling App: %s", err)
	}
	fmt.Println("---")
	fmt.Println(string(bs))
}

func PrintSecret(secret *corev1.Secret) {
	bs, err := yaml.Marshal(secret)
	if err != nil {
		fmt.Errorf("Marshaling Secret: %s", err)
	}

	fmt.Println("---")
	fmt.Println(string(bs))
}
