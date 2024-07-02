package cmd

import (
	"fmt"
	"os"
	"path"
	"strings"

	"github.com/pkg/errors"
	"github.com/spf13/cobra"
	"github.com/vmware-tanzu-labs/educates-training-platform/client-programs/pkg/utils"
)

func (p *ProjectInfo) NewLocalSecretsListCmd() *cobra.Command {
	var c = &cobra.Command{
		Args:  cobra.NoArgs,
		Use:   "list",
		Short: "List secrets in the cache",
		RunE: func(_ *cobra.Command, _ []string) error {
			secretsCacheDir := path.Join(utils.GetEducatesHomeDir(), "secrets")

			err := os.MkdirAll(secretsCacheDir, os.ModePerm)

			if err != nil {
				return errors.Wrapf(err, "unable to create secrets cache directory")
			}

			files, err := os.ReadDir(secretsCacheDir)

			if err != nil {
				return errors.Wrapf(err, "unable to read secrets cache directory")
			}

			for _, f := range files {
				if strings.HasSuffix(f.Name(), ".yaml") {
					name := strings.TrimSuffix(f.Name(), ".yaml")
					fmt.Println(name)
				}
			}

			return nil
		},
	}

	return c
}
