// Copyright 2022 The Educates Authors.

package cmd

import (
	"fmt"
	"io/ioutil"
	"os"
	"path"
	"strings"

	"github.com/adrg/xdg"
	"github.com/pkg/errors"
	"github.com/spf13/cobra"
)

func (p *ProjectInfo) NewSecretsListCmd() *cobra.Command {
	var c = &cobra.Command{
		Args:  cobra.NoArgs,
		Use:   "list",
		Short: "List secrets in the cache",
		RunE: func(_ *cobra.Command, _ []string) error {
			configFileDir := path.Join(xdg.DataHome, "educates")
			secretsCacheDir := path.Join(configFileDir, "secrets")

			err := os.MkdirAll(secretsCacheDir, os.ModePerm)

			if err != nil {
				return errors.Wrapf(err, "unable to create secrets cache directory")
			}

			files, err := ioutil.ReadDir(secretsCacheDir)

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
