package cmd

import (
	"os"
	"path/filepath"

	"github.com/mitchellh/go-homedir"
	"github.com/spf13/cobra"
	"github.com/vmware-tanzu-labs/educates-training-platform/client-programs/pkg/cluster"
	"github.com/vmware-tanzu-labs/educates-training-platform/client-programs/pkg/diagnostics"
)

type AdminDiagnosticsCollectOptions struct {
	Dest       string
	Kubeconfig string
	Verbose    bool
}

func (o *AdminDiagnosticsCollectOptions) Run() error {
	clusterConfig := cluster.NewClusterConfig(o.Kubeconfig)

	diagnostics := diagnostics.NewClusterDiagnostics(clusterConfig, o.Dest, o.Verbose)

	if err := diagnostics.Run(); err != nil {
		return err
	}

	return nil
}

func (p *ProjectInfo) NewAdminDiagnosticsCollectCmd() *cobra.Command {
	var o AdminDiagnosticsCollectOptions

	var c = &cobra.Command{
		Args:  cobra.NoArgs,
		Use:   "collect",
		Short: "Collect diagnostic information for an Educates cluster",
		RunE:  func(_ *cobra.Command, _ []string) error { return o.Run() },
	}

	c.Flags().StringVar(
		&o.Kubeconfig,
		"kubeconfig",
		"",
		"kubeconfig file to use instead of $KUBECONFIG or $HOME/.kube/config",
	)

	c.Flags().StringVar(
		&o.Dest,
		"dest",
		getDefaultFilename(),
		"Path to the directory where the diagnostics files will be generated",
	)

	c.Flags().BoolVar(
		&o.Verbose,
		"verbose",
		false,
		"print verbose output",
	)
	// c.MarkFlagRequired("dest")

	return c
}

func getDefaultFilename() string {
	dir, err := os.Getwd()
	if err != nil {
		dir, err = homedir.Dir()
		if err != nil {
			dir, err = os.MkdirTemp("", "educates-diagnostics")
			if err != nil {
				dir = os.TempDir()
			}
			defer os.RemoveAll(dir)
		}
	}
	return filepath.Join(dir, "educates-diagnostics.tar.gz")
}
