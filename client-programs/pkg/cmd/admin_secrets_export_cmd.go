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
	"golang.org/x/exp/slices"
)

func (p *ProjectInfo) NewAdminSecretsExportCmd() *cobra.Command {
	var c = &cobra.Command{
		Args:  cobra.ArbitraryArgs,
		Use:   "export [NAME]",
		Short: "Export secrets in the cache",
		RunE: func(_ *cobra.Command, args []string) error {
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

			count := 0

			for _, f := range files {
				if strings.HasSuffix(f.Name(), ".yaml") {
					name := strings.TrimSuffix(f.Name(), ".yaml")
					fullPath := path.Join(secretsCacheDir, f.Name())

					if len(args) == 0 || slices.Contains(args, name) {
						yamlData, err := os.ReadFile(fullPath)

						if err != nil {
							continue
						}

						if len(yamlData) == 0 || string(yamlData) == "\n" {
							continue
						}

						if count != 0 {
							fmt.Println("---")
						}

						fmt.Print(string(yamlData))

						count = count + 1
					}
				}
			}

			return nil
		},
	}

	return c
}
