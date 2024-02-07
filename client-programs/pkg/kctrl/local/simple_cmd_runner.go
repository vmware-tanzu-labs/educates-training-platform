// Copyright 2022 VMware, Inc.
// SPDX-License-Identifier: Apache-2.0

package local

import (
	"fmt"
	"io"
	"os"
	goexec "os/exec"

	"github.com/vmware-tanzu/carvel-kapp-controller/pkg/exec"
)

type SimpleCmdRunner struct {
	log io.Writer
}

var _ exec.CmdRunner = &SimpleCmdRunner{}

func NewSimpleCmdRunner(log io.Writer) *SimpleCmdRunner {
	return &SimpleCmdRunner{log}
}

func (r SimpleCmdRunner) Run(cmd *goexec.Cmd) error {
	// Adding os environment keys to cmd environment
	cmd.Env = append(os.Environ(), cmd.Env...)

	fmt.Fprintf(r.log, ".")
	defer fmt.Fprintf(r.log, ".")

	return exec.PlainCmdRunner{}.Run(cmd)
}

func (r SimpleCmdRunner) RunWithCancel(cmd *goexec.Cmd, cancelCh chan struct{}) error {
	fmt.Fprintf(r.log, ".")
	defer fmt.Fprintf(r.log, ".")

	return exec.PlainCmdRunner{}.RunWithCancel(cmd, cancelCh)
}
