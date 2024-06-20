package cmd

import (
	"os"
	"path"
	"regexp"

	"github.com/pkg/errors"
	"github.com/spf13/cobra"
	"github.com/vmware-tanzu-labs/educates-training-platform/client-programs/pkg/utils"
)

func (p *ProjectInfo) NewLocalSecretsRemoveCmd() *cobra.Command {
	var c = &cobra.Command{
		Args:  cobra.ExactArgs(1),
		Use:   "remove NAME",
		Short: "Remove secret from the cache",
		RunE: func(_ *cobra.Command, args []string) error {
			name := args[0]

			var err error
			var matched bool

			if matched, err = regexp.MatchString("^[a-z0-9]([.a-z0-9-]+)?[a-z0-9]$", name); err != nil {
				return errors.Wrapf(err, "regex match on secret name failed")
			}

			if !matched {
				return errors.Errorf("invalid secret name %q", name)
			}

			secretsCacheDir := path.Join(utils.GetEducatesHomeDir(), "secrets")

			secretFilePath := path.Join(secretsCacheDir, name+".yaml")

			os.Remove(secretFilePath)

			return nil
		},
	}

	return c
}
