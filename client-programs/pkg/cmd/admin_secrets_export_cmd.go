package cmd

import (
	"os"
	"path"

	"github.com/pkg/errors"
	"github.com/spf13/cobra"

	"github.com/vmware-tanzu-labs/educates-training-platform/client-programs/pkg/utils"
)

func (p *ProjectInfo) NewAdminSecretsExportCmd() *cobra.Command {
	var c = &cobra.Command{
		Args:  cobra.ArbitraryArgs,
		Use:   "export [NAME]",
		Short: "Export secrets in the cache",
		RunE: func(_ *cobra.Command, args []string) error {
			secretsCacheDir := path.Join(utils.GetEducatesHomeDir(), "secrets")

			err := os.MkdirAll(secretsCacheDir, os.ModePerm)

			if err != nil {
				return errors.Wrapf(err, "unable to create secrets cache directory")
			}

			err = utils.PrintYamlFilesInDir(secretsCacheDir, args)
			if err != nil {
				return errors.Wrapf(err, "unable to read secrets cache directory")
			}

			return nil
		},
	}

	return c
}
