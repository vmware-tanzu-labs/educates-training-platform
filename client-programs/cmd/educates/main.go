/*
Command line client for Educates.
*/
package main

import (
	"os"
	"strings"

	"github.com/go-logr/logr"
	"github.com/vmware-tanzu-labs/educates-training-platform/client-programs/pkg/cmd"
	"k8s.io/klog/v2"
	logf "sigs.k8s.io/controller-runtime/pkg/log"
)

// NOTE: The version of Educates which is installed by the CLI is overridden
// with the actual version at build time when making a release.

var projectVersion string = "develop"
var imageRepository string = "ghcr.io/vmware-tanzu-labs"

// Main entrypoint for execution of Educates CLI.

func main() {
	// All the functions for setting up commands are implemented as receiver
	// functions on ProjectInfo object so they can have access to compiled in
	// default values such as the release version of Educates.
	log := logr.New(logf.NullLogSink{}) //zap.New(zap.UseDevMode(false))
	logf.SetLogger(log)                 // This one is used in the reconciler code
	klog.SetLogger(log)                 // This one is used in the k8s client-go code

	p := cmd.NewProjectInfo(strings.TrimSpace(projectVersion), strings.TrimSpace(imageRepository))

	c := p.NewEducatesCmdGroup()

	// Execute the actual command with arguments sourced from os.Args.

	err := c.Execute()

	if err != nil {
		os.Exit(1)
	}
}
