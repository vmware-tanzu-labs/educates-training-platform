// Copyright 2022 VMware, Inc.
// SPDX-License-Identifier: Apache-2.0

package local

import (
	"fmt"
	"io"
	"os"
	goexec "os/exec"
	"path/filepath"

	"github.com/vmware-tanzu/carvel-kapp-controller/pkg/exec"
)

type DetailedCmdRunner struct {
	log     io.Writer
	verbose bool
}

var _ exec.CmdRunner = &DetailedCmdRunner{}

/**
 * NewDetailedCmdRunner logs additiona information to the writter
 * before and after each command run
 * and does also print any output from the command when verbose is true
 */
func NewDetailedCmdRunner(log io.Writer, verbose bool) *DetailedCmdRunner {
	return &DetailedCmdRunner{log, verbose}
}

func (r DetailedCmdRunner) Run(cmd *goexec.Cmd) error {

	// TODO: This might be a bit too specific to kapp, we should probably
	// have a more generic way to handle this. Also, it might be specific to macOS and Linux
	if r.verbose && filepath.Base(cmd.Path) == "kapp" {
		cmd.Stdout = io.MultiWriter(r.log, cmd.Stdout)
		cmd.Stderr = io.MultiWriter(r.log, cmd.Stderr)
	}

	// Adding os environment keys to cmd environment
	cmd.Env = append(os.Environ(), cmd.Env...)

	if r.verbose {
		fmt.Fprintf(r.log, "==> Executing %s %v\n", cmd.Path, cmd.Args)
		defer fmt.Fprintf(r.log, "==> Finished executing %s\n\n", cmd.Path)
	} else {
		fmt.Fprintf(r.log, ".")
		defer fmt.Fprintf(r.log, ".")
	}

	return exec.PlainCmdRunner{}.Run(cmd)
}

func (r DetailedCmdRunner) RunWithCancel(cmd *goexec.Cmd, cancelCh chan struct{}) error {
	if r.verbose {
		cmd.Stdout = io.MultiWriter(r.log, cmd.Stdout)
		cmd.Stderr = io.MultiWriter(r.log, cmd.Stderr)
	}

	if r.verbose {
		fmt.Fprintf(r.log, "==> Executing %s %v\n", cmd.Path, cmd.Args)
		defer fmt.Fprintf(r.log, "==> Finished executing %s\n\n", cmd.Path)
	} else {
		fmt.Fprintf(r.log, ".")
		defer fmt.Fprintf(r.log, ".")
	}

	return exec.PlainCmdRunner{}.RunWithCancel(cmd, cancelCh)
}
