package cmd

import (
	"github.com/pkg/errors"
	"github.com/spf13/cobra"
	"github.com/vmware-tanzu-labs/educates-training-platform/client-programs/pkg/cluster"
	"github.com/vmware-tanzu-labs/educates-training-platform/client-programs/pkg/diagnostics"
)

type AdminClusterDiagnosticsOptions struct {
	Dir        string
	File       string
	Kubeconfig string
	DryRun     bool
	Verbose    bool
}

func (o *AdminClusterDiagnosticsOptions) Run() error {
	if o.Dir == "" && o.File == "" {
		return errors.New("either --dir or --file must be provided")
	}
	clusterConfig := cluster.NewClusterConfig(o.Kubeconfig)

	diagnostics := diagnostics.NewClusterDiagnostics(clusterConfig, o.Dir, o.File)

	if err := diagnostics.Run(); err != nil {
		return err
	}

	return nil
}

func (p *ProjectInfo) NewAdminClusterDiagnosticsCmd() *cobra.Command {
	var o AdminClusterDiagnosticsOptions

	var c = &cobra.Command{
		Args:  cobra.NoArgs,
		Use:   "diagnostics",
		Short: "Gets diagnostic information for an Educates cluster",
		RunE:  func(_ *cobra.Command, _ []string) error { return o.Run() },
	}

	c.Flags().StringVar(
		&o.Kubeconfig,
		"kubeconfig",
		"",
		"kubeconfig file to use instead of $KUBECONFIG or $HOME/.kube/config",
	)

	c.Flags().StringVar(
		&o.Dir,
		"dir",
		"",
		"Path to the directory where the diagnostics files will be generated",
	)
	c.Flags().StringVar(
		&o.File,
		"file",
		"",
		"Full path and filename for the generated compressed (.tar.gz) diagnostics file",
	)

	c.Flags().BoolVar(
		&o.DryRun,
		"dry-run",
		false,
		"prints to stdout the yaml that would be deployed to the cluster",
	)
	c.Flags().BoolVar(
		&o.Verbose,
		"verbose",
		false,
		"print verbose output",
	)
	// c.MarkFlagRequired("provider")

	return c
}
