// Copyright 2022 VMware, Inc.
// SPDX-License-Identifier: Apache-2.0

package local

import (
	"context"
	"fmt"
	gourl "net/url"
	"os"
	"time"

	deployments "github.com/vmware-tanzu-labs/educates-training-platform/client-programs/pkg/kctrl/deployments"
	"github.com/vmware-tanzu-labs/educates-training-platform/client-programs/pkg/kctrl/logger"
	kcv1alpha1 "github.com/vmware-tanzu/carvel-kapp-controller/pkg/apis/kappctrl/v1alpha1"
	"github.com/vmware-tanzu/carvel-kapp-controller/pkg/app"
	fakekc "github.com/vmware-tanzu/carvel-kapp-controller/pkg/client/clientset/versioned/fake"
	"github.com/vmware-tanzu/carvel-kapp-controller/pkg/componentinfo"
	kcconfig "github.com/vmware-tanzu/carvel-kapp-controller/pkg/config"
	"github.com/vmware-tanzu/carvel-kapp-controller/pkg/exec"
	"github.com/vmware-tanzu/carvel-kapp-controller/pkg/kubeconfig"
	"github.com/vmware-tanzu/carvel-kapp-controller/pkg/memdir"
	"github.com/vmware-tanzu/carvel-kapp-controller/pkg/metrics"
	"github.com/vmware-tanzu/carvel-kapp-controller/pkg/reftracker"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/runtime"
	"k8s.io/apimachinery/pkg/types"
	"k8s.io/client-go/kubernetes"
	logf "sigs.k8s.io/controller-runtime/pkg/log"
	"sigs.k8s.io/controller-runtime/pkg/reconcile"
)

type Reconciler struct {
	coreClient kubernetes.Interface
	restHost   string
	cmdRunner  exec.CmdRunner
	logger     logger.KctrlLogger
}

func NewReconciler(coreClient kubernetes.Interface, restHost string,
	cmdRunner exec.CmdRunner, logger logger.KctrlLogger) *Reconciler {
	return &Reconciler{coreClient, restHost, cmdRunner, logger}
}

type ReconcileOpts struct {
	Delete          bool
	DeployResources bool
}

func (o *Reconciler) ReconcileDeployments(configs deployments.Deployments, opts ReconcileOpts) error {
	var objs []runtime.Object
	var appRes kcv1alpha1.App
	// var primaryAnns map[string]string

	appRes = configs.App
	// primaryAnns = appRes.Annotations
	if opts.Delete {
		appRes.DeletionTimestamp = &metav1.Time{time.Now()}
	}
	objs = append(objs, &appRes)

	// TODO: A CoreClient will always need to be instantiated, because we're always going to deploy resources
	var coreClient kubernetes.Interface
	if opts.DeployResources {
		// An instance coreClient is only instantiated if resources are going to be deployed
		coreClient = o.coreClient
		err := o.hackyConfigureKubernetesDst(coreClient)
		if err != nil {
			return err
		}
	}

	minCoreClient := &MinCoreClient{
		// This is a nil interface when we do not expect resources to be deployed
		// Only the dev command requires an instance of coreClient to be supplied here
		client:      coreClient,
		localSecret: &localSecret{configs.Secret},
	}
	kcClient := fakekc.NewSimpleClientset(objs...)

	appReconciler := o.newReconcilers(minCoreClient, kcClient, opts)

	// TODO is there a better way to deal with service accounts?
	// TODO do anything with reconcile result?
	_, reconcileErr := appReconciler.Reconcile(context.TODO(), reconcile.Request{
		NamespacedName: types.NamespacedName{
			Name:      appRes.Name,
			Namespace: appRes.Namespace,
		},
	})
	// TODO: Find a way to report that reconciliation failed, as neither reconcileErr nor result.RequeueAfter will have
	// valuable information

	return reconcileErr
}

// hackyConfigureKubernetesDst configures environment variables for kapp.
// This would not be necessary if kapp was using default kubeconfig; however,
// right now kapp will use configuration based on configured serviceAccount within
// PackageInstall or App CR. However, we still need to configure it to know where to connect.
func (o *Reconciler) hackyConfigureKubernetesDst(coreClient kubernetes.Interface) error {
	host := o.restHost
	hostURL, err := gourl.Parse(host)
	if err != nil {
		return fmt.Errorf("Parsing host: %s", err)
	}
	os.Setenv("KUBERNETES_SERVICE_HOST", hostURL.Hostname())
	if hostURL.Port() == "" {
		os.Setenv("KUBERNETES_SERVICE_PORT", "443")
	} else {
		os.Setenv("KUBERNETES_SERVICE_PORT", hostURL.Port())
	}

	cm, err := coreClient.CoreV1().ConfigMaps("kube-public").Get(context.TODO(), "kube-root-ca.crt", metav1.GetOptions{})
	if err != nil {
		return fmt.Errorf("Fetching kube-root-ca.crt: %s", err)
	}
	// Used during fetching of service accounts in kapp-controller
	os.Setenv("KAPPCTRL_KUBERNETES_CA_DATA", cm.Data["ca.crt"])

	return nil
}

func (o *Reconciler) newReconcilers(
	coreClient kubernetes.Interface, kcClient *fakekc.Clientset,
	// vendirConfigHook func(vendirconf.Config) vendirconf.Config,
	opts ReconcileOpts) *app.Reconciler {

	runLog := logf.Log.WithName("deploy")

	kcConfig := &kcconfig.Config{}

	appMetrics := metrics.NewAppMetrics()
	appMetrics.RegisterAllMetrics()

	refTracker := reftracker.NewAppRefTracker()
	updateStatusTracker := reftracker.NewAppUpdateStatus()

	kubeConfig := kubeconfig.NewKubeconfig(coreClient, runLog)
	compInfo := componentinfo.NewComponentInfo(coreClient, kubeConfig, "dev")

	cacheFolderPkgRepoApps := memdir.NewTmpDir("cache-package-repo")

	appFactory := app.CRDAppFactory{
		CoreClient: coreClient,
		AppClient:  kcClient,
		KcConfig:   kcConfig,
		AppMetrics: appMetrics,
		// VendirConfigHook: vendirConfigHook,
		KbldAllowBuild: false,
		CmdRunner:      o.cmdRunner,
		CompInfo:       compInfo,
		CacheFolder:    cacheFolderPkgRepoApps,
		Kubeconf:       kubeConfig,
	}
	appReconciler := app.NewReconciler(kcClient, runLog.WithName("app"),
		appFactory, refTracker, updateStatusTracker, compInfo)

	return appReconciler
}
