package installer

import (
	"context"
	"fmt"
	"os"
	"path/filepath"

	"carvel.dev/imgpkg/pkg/imgpkg/registry"
	imgpkgv1 "carvel.dev/imgpkg/pkg/imgpkg/v1"
	"github.com/pkg/errors"
	"github.com/vmware-tanzu-labs/educates-training-platform/client-programs/pkg/cluster"
	"github.com/vmware-tanzu-labs/educates-training-platform/client-programs/pkg/config"
	deployments "github.com/vmware-tanzu-labs/educates-training-platform/client-programs/pkg/kctrl/deployments"
	"github.com/vmware-tanzu-labs/educates-training-platform/client-programs/pkg/kctrl/dev"
	"github.com/vmware-tanzu-labs/educates-training-platform/client-programs/pkg/kctrl/logger"
	cmdtpl "github.com/vmware-tanzu/carvel-ytt/pkg/cmd/template"
	yttUI "github.com/vmware-tanzu/carvel-ytt/pkg/cmd/ui"
	"github.com/vmware-tanzu/carvel-ytt/pkg/files"
	"github.com/vmware-tanzu/carvel-ytt/pkg/yamlmeta"
	"gopkg.in/yaml.v2"
	apiv1 "k8s.io/api/core/v1"
	"k8s.io/client-go/kubernetes"

	rbacv1 "k8s.io/api/rbac/v1"
	k8serrors "k8s.io/apimachinery/pkg/api/errors"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
)

const EducatesInstallerImageRef = "quay.io/failk8s/educates-cluster-essentials-package:develop"

type Installer struct {
	Deployments deployments.Deployments
	Debug       bool
}

func NewInstaller() *Installer {
	return &Installer{}
}

func (inst *Installer) Run(version string, packageRepository string, fullConfig *config.InstallationConfig, clusterConfig *cluster.ClusterConfig) error {
	fmt.Println("Installing educates ...")

	client, err := clusterConfig.GetClient()
	if err != nil {
		return err
	}

	// TODO: Check to see if educates-installer namespace is in destroying state and wait for it to be deleted

	err = inst.createRBAC(client)
	if err != nil {
		return err
	}

	// Create the Deployment Descriptors
	installObjs, err := deployments.NewDeploymentsForInstall(fullConfig, inst.getBundleImageRef(version, packageRepository))
	if err != nil {
		panic(err)
	}
	if inst.Debug {
		deployments.PrintApp(&installObjs.App)
		deployments.PrintSecret(&installObjs.Secret)
	}
	inst.Deployments = installObjs

	config, err := clusterConfig.GetConfig()
	if err != nil {
		return err
	}
	NewInstallerPrinterImpl().printTarget(config)

	devInstance := dev.NewDevOptions(client, config.Host, logger.NewKctrlStdoutLogger())
	devInstance.RunWithDescriptors(inst.Deployments)

	err = inst.deleteRBAC(client, false)
	if err != nil {
		return err
	}

	return nil
}

func (inst *Installer) Delete(fullConfig *config.InstallationConfig, clusterConfig *cluster.ClusterConfig) error {
	fmt.Println("Deleting educates ...")

	client, err := clusterConfig.GetClient()
	if err != nil {
		return err
	}

	err = inst.createRBAC(client)
	if err != nil {
		return err
	}

	// Create the Deployment Descriptors
	installObjs, err := deployments.NewDeploymentsForDelete(fullConfig)
	if err != nil {
		panic(err)
	}
	if inst.Debug {
		deployments.PrintApp(&installObjs.App)
		deployments.PrintSecret(&installObjs.Secret)
	}
	inst.Deployments = installObjs

	config, err := clusterConfig.GetConfig()
	if err != nil {
		return err
	}
	NewInstallerPrinterImpl().printTarget(config)

	devInstance := dev.NewDevOptions(client, config.Host, logger.NewKctrlStdoutLogger())
	devInstance.Delete = true

	devInstance.RunWithDescriptors(inst.Deployments)

	err = inst.deleteRBAC(client, true)
	if err != nil {
		return err
	}

	return nil
}

func (inst *Installer) DryRun(version string, packageRepository string, fullConfig *config.InstallationConfig) ([]*yamlmeta.Document, error) {

	// Create a temporary directory
	tempDir, err := os.MkdirTemp("", "educates-installer")
	if err != nil {
		return nil, err
	}
	defer os.RemoveAll(tempDir) // clean up

	pullOpts := imgpkgv1.PullOpts{
		Logger:   logger.NewImgpkgNoopLoggerImpl(),
		AsImage:  false,
		IsBundle: true,
	}
	filePath := filepath.Join(tempDir, "bundle-out")
	// TODO: Remove some logging from here
	_, err = imgpkgv1.Pull(inst.getBundleImageRef(version, packageRepository), filePath, pullOpts, registry.Opts{})
	if err != nil {
		return nil, err
	}

	filesToProcess, err := files.NewSortedFilesFromPaths([]string{filepath.Join(filePath, "config/ytt/")}, files.SymlinkAllowOpts{})
	if err != nil {
		return nil, err
	}

	// Use ytt to generate the yaml for the cluster packages
	ui := yttUI.NewTTY(false)
	opts := cmdtpl.NewOptions()

	yamlBytes, err := yaml.Marshal(fullConfig)
	if err != nil {
		return nil, err
	}

	opts.DataValuesFlags = cmdtpl.DataValuesFlags{
		FromFiles: []string{"values"},
		ReadFilesFunc: func(path string) ([]*files.File, error) {
			switch path {
			case "values":
				return []*files.File{
					files.MustNewFileFromSource(files.NewBytesSource("values/values.yaml", yamlBytes)),
				}, nil
			default:
				return nil, fmt.Errorf("unknown file '%s'", path)
			}
		},
	}

	out := opts.RunWithFiles(cmdtpl.Input{Files: filesToProcess}, ui)

	// When we get errors in ytt processing, e.g. because of schema validation, out.Err is not nil
	if out.Err != nil {
		fmt.Println(out.Err)
	}

	return out.DocSet.Items, nil
}

func (inst *Installer) createRBAC(client *kubernetes.Clientset) error {
	namespacesClient := client.CoreV1().Namespaces()
	_, err := namespacesClient.Get(context.TODO(), deployments.EducatesInstallerString, metav1.GetOptions{})

	if k8serrors.IsNotFound(err) {
		namespaceObj := apiv1.Namespace{
			ObjectMeta: metav1.ObjectMeta{
				Name: deployments.EducatesInstallerString,
			},
		}

		_, err = namespacesClient.Create(context.TODO(), &namespaceObj, metav1.CreateOptions{})

		if err != nil {
			return errors.Wrap(err, "unable to educates-installer namespace")
		}
	}

	serviceAccountsClient := client.CoreV1().ServiceAccounts(deployments.EducatesInstallerString)
	_, err = serviceAccountsClient.Get(context.TODO(), deployments.EducatesInstallerString, metav1.GetOptions{})

	if k8serrors.IsNotFound(err) {
		serviceAccount := &apiv1.ServiceAccount{
			ObjectMeta: metav1.ObjectMeta{
				Name: deployments.EducatesInstallerString,
			},
		}

		_, err = serviceAccountsClient.Create(context.TODO(), serviceAccount, metav1.CreateOptions{})

		if err != nil {
			return errors.Wrap(err, "unable to create services service account")
		}
	}

	clusterRoleBindingClient := client.RbacV1().ClusterRoleBindings()
	_, err = clusterRoleBindingClient.Get(context.TODO(), deployments.EducatesInstallerString, metav1.GetOptions{})

	if k8serrors.IsNotFound(err) {
		clusterRoleBinding := &rbacv1.ClusterRoleBinding{
			ObjectMeta: metav1.ObjectMeta{
				Name: deployments.EducatesInstallerString,
			},
			RoleRef: rbacv1.RoleRef{
				APIGroup: "rbac.authorization.k8s.io",
				Kind:     "ClusterRole",
				Name:     "cluster-admin",
			},
			Subjects: []rbacv1.Subject{
				{
					Kind:      "ServiceAccount",
					Name:      deployments.EducatesInstallerString,
					Namespace: deployments.EducatesInstallerString,
				},
			},
		}

		_, err = clusterRoleBindingClient.Create(context.TODO(), clusterRoleBinding, metav1.CreateOptions{})

		if err != nil {
			return errors.Wrap(err, "unable to create services role binding")
		}
	}

	return nil
}

func (inst *Installer) getBundleImageRef(version string, packageRepository string) string {
	var bundleImageRef string

	if version == "latest" {
		bundleImageRef = "registry.default.svc.cluster.local/educates-training-platform:0.0.1"
	} else {
		// TODO: Uncomment below line when package is properly built
		// bundleImageRef = fmt.Sprintf("%s/educates-training-platform:%s", packageRepository, version)
		bundleImageRef = EducatesInstallerImageRef
	}
	return bundleImageRef
}

func (inst *Installer) deleteRBAC(client *kubernetes.Clientset, deleteNS bool) error {

	clusterRoleBindingClient := client.RbacV1().ClusterRoleBindings()
	crb, err := clusterRoleBindingClient.Get(context.TODO(), deployments.EducatesInstallerString, metav1.GetOptions{})
	if crb != nil {
		err = clusterRoleBindingClient.Delete(context.TODO(), deployments.EducatesInstallerString, metav1.DeleteOptions{})
		if err != nil {
			return errors.Wrap(err, "unable to delete services role binding")
		}
	}
	if err != nil {
		return errors.Wrap(err, "unable to delete services role binding")
	}

	// ----------------------------

	serviceAccountsClient := client.CoreV1().ServiceAccounts(deployments.EducatesInstallerString)

	sa, err := serviceAccountsClient.Get(context.TODO(), deployments.EducatesInstallerString, metav1.GetOptions{})
	if sa != nil {
		err = serviceAccountsClient.Delete(context.TODO(), deployments.EducatesInstallerString, metav1.DeleteOptions{})
		if err != nil {
			return errors.Wrap(err, "unable to delete service account")
		}
	}
	if err != nil {
		return errors.Wrap(err, "unable to delete service account")
	}

	// ----------------------------

	if deleteNS {
		namespacesClient := client.CoreV1().Namespaces()

		ns, err := namespacesClient.Get(context.TODO(), deployments.EducatesInstallerString, metav1.GetOptions{})

		if ns != nil {
			err = namespacesClient.Delete(context.TODO(), deployments.EducatesInstallerString, metav1.DeleteOptions{})

			if err != nil {
				return errors.Wrap(err, "unable to delete educates-installer namespace")
			}
		}
		if err != nil {
			return errors.Wrap(err, "unable to delete educates-installer namespace")
		}
	}

	return nil
}
