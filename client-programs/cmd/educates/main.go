// Copyright 2022 The Educates Authors.

/*
Command line client for Educates.
*/
package main

import (
	"os"
	"strings"

	"github.com/vmware-tanzu-labs/educates-training-platform/client-programs/pkg/cmd"
)

// NOTE: The version of Educates which is installed by the CLI is overridden
// with the actual version at build time when making a release.

var projectVersion string = "develop"

// Main entrypoint for execution of Educates CLI.

func main() {
	// All the functions for setting up commands are implemented as receiver
	// functions on ProjectInfo object so they can have access to compiled in
	// default values such as the release version of Educates.

	p := cmd.NewProjectInfo(strings.TrimSpace(projectVersion))

	c := p.NewEducatesCmdGroup()

	// Execute the actual command with arguments sourced from os.Args.

	err := c.Execute()

	if err != nil {
		os.Exit(1)
	}
}
