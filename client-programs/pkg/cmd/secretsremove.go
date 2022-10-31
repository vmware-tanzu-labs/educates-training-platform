/*
Copyright © 2022 The Educates Authors.
*/
package cmd

import (
	"os"
	"path"
	"regexp"

	"github.com/adrg/xdg"
	"github.com/pkg/errors"
	"github.com/spf13/cobra"
)

func NewSecretsRemoveCmd() *cobra.Command {
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

			configFileDir := path.Join(xdg.DataHome, "educates")
			secretsCacheDir := path.Join(configFileDir, "secrets")

			secretFilePath := path.Join(secretsCacheDir, name+".yaml")

			os.Remove(secretFilePath)

			return nil
		},
	}

	return c
}
