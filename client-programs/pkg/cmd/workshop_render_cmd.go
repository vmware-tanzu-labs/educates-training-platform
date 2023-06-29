// Copyright 2022-2023 The Educates Authors.

package cmd

import (
	"os"
	"path/filepath"

	"github.com/pkg/errors"
	"github.com/spf13/cobra"

	"github.com/vmware-tanzu-labs/educates-training-platform/client-programs/pkg/renderer"
)

type WorkshopRenderOptions struct {
	Kubeconfig string
	Session    string
	Port       int
}

func (p *ProjectInfo) NewWorkshopRenderCmd() *cobra.Command {
	var o WorkshopRenderOptions

	var c = &cobra.Command{
		Args:  cobra.MaximumNArgs(1),
		Use:   "render [PATH]",
		Short: "Render workshop instructions",
		RunE: func(_ *cobra.Command, args []string) error {
			var err error

			var directory string

			if len(args) != 0 {
				directory = filepath.Clean(args[0])
			} else {
				directory = "."
			}

			if directory, err = filepath.Abs(directory); err != nil {
				return errors.Wrap(err, "couldn't convert workshop directory to absolute path")
			}

			fileInfo, err := os.Stat(directory)

			if err != nil || !fileInfo.IsDir() {
				return errors.New("workshop directory does not exist or path is not a directory")
			}

			return renderer.RunHugoServer(filepath.Join(directory, "workshop"), o.Kubeconfig, o.Session, o.Port)
		},
	}

	c.Flags().StringVar(
		&o.Kubeconfig,
		"kubeconfig",
		"",
		"kubeconfig file to use instead of $KUBECONFIG or $HOME/.kube/config",
	)
	c.Flags().StringVar(
		&o.Session,
		"session",
		"",
		"the name of the workshop session",
	)
	c.Flags().IntVar(
		&o.Port,
		"port",
		1313,
		"port on which the server will listen",
	)

	c.MarkFlagRequired("session")

	return c
}
