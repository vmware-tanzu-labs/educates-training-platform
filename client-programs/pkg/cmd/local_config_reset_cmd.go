package cmd

import (
	"os"
	"path"

	"github.com/spf13/cobra"
	"github.com/vmware-tanzu-labs/educates-training-platform/client-programs/pkg/utils"
)

func (p *ProjectInfo) NewLocalConfigResetCmd() *cobra.Command {
	var c = &cobra.Command{
		Args:  cobra.NoArgs,
		Use:   "reset",
		Short: "Reset local configuration",
		RunE: func(_ *cobra.Command, _ []string) error {
			valuesFile := path.Join(utils.GetEducatesHomeDir(), "values.yaml")

			os.Remove(valuesFile)

			return nil
		},
	}

	return c
}
