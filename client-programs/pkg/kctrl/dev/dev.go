// Copyright 2020 VMware, Inc.
// SPDX-License-Identifier: Apache-2.0

package dev

import (
	"context"
	"fmt"
	"os"
	"time"

	deployments "github.com/vmware-tanzu-labs/educates-training-platform/client-programs/pkg/kctrl/deployments"
	cmdlocal "github.com/vmware-tanzu-labs/educates-training-platform/client-programs/pkg/kctrl/local"
	"github.com/vmware-tanzu-labs/educates-training-platform/client-programs/pkg/kctrl/logger"
	kcv1alpha1 "github.com/vmware-tanzu/carvel-kapp-controller/pkg/apis/kappctrl/v1alpha1"
	fakekc "github.com/vmware-tanzu/carvel-kapp-controller/pkg/client/clientset/versioned/fake"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/client-go/kubernetes"
	"sigs.k8s.io/yaml"
)

type DevOptions struct {
	// TODO: Replace with proper Logger
	// ui          ui.UI
	// depsFactory cmdcore.DepsFactory
	coreClient kubernetes.Interface
	restHost   string
	logger     logger.KctrlLogger

	Files  []string
	Delete bool
	Debug  bool
}

func NewDevOptions(coreClient kubernetes.Interface, restHost string, logger logger.KctrlLogger) *DevOptions {
	return &DevOptions{
		coreClient: coreClient,
		restHost:   restHost,
		logger:     logger,
		Debug:      true,
	}
}

func (o *DevOptions) RunWithDescriptors(configs deployments.Deployments) error {
	// When second param is true, every step`s output in reconciler will be printed
	// TODO: Decide whether to use os.Stdout or not and whether to log all or not
	cmdRunner := cmdlocal.NewDetailedCmdRunner(os.Stdout, false)

	// Obtains an instance of the local reconciler. This reconciler will be used
	// to reconcile the App CR in memory and then apply it into the cluster.
	reconciler := cmdlocal.NewReconciler(o.coreClient, o.restHost, cmdRunner, o.logger)

	// Does the reconciliation
	reconcileErr := reconciler.ReconcileDeployments(configs, cmdlocal.ReconcileOpts{
		Delete:          o.Delete,
		Debug:           o.Debug,
		DeployResources: true,

		// TODO: These print more information on output. We need to decide whether this is useful or not
		// BeforeAppReconcile: o.beforeAppReconcile,
		// AfterAppReconcile:  o.afterAppReconcile,
	})

	// TODO app watcher needs a little time to run; should block ideally
	time.Sleep(100 * time.Millisecond)

	return reconcileErr
}

func (o *DevOptions) beforeAppReconcile(app kcv1alpha1.App, kcClient *fakekc.Clientset) error {
	err := o.printRs(app.ObjectMeta, kcClient)
	if err != nil {
		return err
	}

	fmt.Printf("Reconciling in-memory app/%s (namespace: %s) ...", app.Name, app.Namespace)

	// go func() {
	// 	appWatcher := cmdapp.NewAppTailer(app.Namespace, app.Name,
	// 		o.ui, kcClient, cmdapp.AppTailerOpts{IgnoreNotExists: true})

	// 	err := appWatcher.TailAppStatus()
	// 	if err != nil {
	// 		o.ui.PrintLinef("App tailing error: %s", err)
	// 	}
	// }()

	return nil
}

func (o *DevOptions) afterAppReconcile(app kcv1alpha1.App, kcClient *fakekc.Clientset) error {
	if o.Debug {
		return o.printRs(app.ObjectMeta, kcClient)
	}
	return nil
}

func (o *DevOptions) printRs(nsName metav1.ObjectMeta, kcClient *fakekc.Clientset) error {
	app, err := kcClient.KappctrlV1alpha1().Apps(nsName.Namespace).Get(context.Background(), nsName.Name, metav1.GetOptions{})
	if err == nil {
		bs, err := yaml.Marshal(app)
		if err != nil {
			return fmt.Errorf("Marshaling App CR: %s", err)
		}

		fmt.Println(string(bs))
	}

	return nil
}
