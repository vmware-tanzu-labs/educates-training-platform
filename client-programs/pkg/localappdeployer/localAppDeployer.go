// Copyright 2020 VMware, Inc.
// SPDX-License-Identifier: Apache-2.0

package localappdeployer

import (
	"os"
	"time"

	deployments "github.com/vmware-tanzu-labs/educates-training-platform/client-programs/pkg/localappdeployer/deployments"
	cmdlocal "github.com/vmware-tanzu-labs/educates-training-platform/client-programs/pkg/localappdeployer/local"
	"github.com/vmware-tanzu-labs/educates-training-platform/client-programs/pkg/localappdeployer/logger"
	"github.com/vmware-tanzu/carvel-kapp-controller/pkg/exec"
	"k8s.io/client-go/kubernetes"
)

type LocalAppDeployerOptions struct {
	coreClient kubernetes.Interface
	restHost   string
	logger     logger.KctrlLogger

	Files   []string
	Delete  bool
	Verbose bool
}

func NewLocalAppDeployerOptions(coreClient kubernetes.Interface, restHost string, logger logger.KctrlLogger, verbose bool) *LocalAppDeployerOptions {
	return &LocalAppDeployerOptions{
		coreClient: coreClient,
		restHost:   restHost,
		logger:     logger,
		Verbose:    verbose,
	}
}

func (o *LocalAppDeployerOptions) RunWithDescriptors(configs deployments.Deployments) error {
	// When second param is true, every step`s output in reconciler will be printed
	// TODO: Decide whether to use os.Stdout or not and whether to log all or not
	var cmdRunner exec.CmdRunner
	if o.Verbose {
		cmdRunner = cmdlocal.NewDetailedCmdRunner(os.Stdout, true)
	} else {
		// cmdRunner = exec.NewPlainCmdRunner()
		cmdRunner = cmdlocal.NewSimpleCmdRunner(os.Stdout)
	}

	// Obtains an instance of the local reconciler. This reconciler will be used
	// to reconcile the App CR in memory and then apply it into the cluster.
	reconciler := cmdlocal.NewReconciler(o.coreClient, o.restHost, cmdRunner, o.logger)

	// Does the reconciliation
	reconcileOpts := cmdlocal.ReconcileOpts{
		Delete:          o.Delete,
		DeployResources: true,
	}
	reconcileErr := reconciler.ReconcileDeployments(configs, reconcileOpts)

	// TODO app watcher needs a little time to run; should block ideally
	time.Sleep(100 * time.Millisecond)

	return reconcileErr
}
