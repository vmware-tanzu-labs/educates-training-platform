/*
Copyright © 2022 The Educates Authors.
*/
package cmd

import (
	"fmt"
	"os"
	"os/exec"
	"path"

	"github.com/adrg/xdg"
	"github.com/pkg/errors"
	"github.com/spf13/cobra"
	"github.com/vmware-tanzu-labs/educates-training-platform/client-programs/pkg/config"
)

func NewConfigEditCmd() *cobra.Command {
	var c = &cobra.Command{
		Args:  cobra.NoArgs,
		Use:   "edit",
		Short: "Edit default configuration",
		RunE: func(_ *cobra.Command, _ []string) error {
			configFileDir := path.Join(xdg.DataHome, "educates")
			valuesFilePath := path.Join(configFileDir, "values.yaml")
			tmpValuesFilePath := fmt.Sprintf("%s.%d", valuesFilePath, os.Getpid())

			tmpValuesFile, err := os.OpenFile(tmpValuesFilePath, os.O_RDWR|os.O_CREATE|os.O_TRUNC, os.ModePerm)

			if err != nil {
				return errors.Wrapf(err, "unable to temporary values file %q", tmpValuesFilePath)
			}

			valuesFileData, err := os.ReadFile(valuesFilePath)

			if err == nil && len(valuesFileData) != 0 {
				tmpValuesFile.Write(valuesFileData)
			}

			tmpValuesFile.Close()

			defer os.Remove(tmpValuesFilePath)

			editor := "vi"

			if s := os.Getenv("EDITOR"); s != "" {
				editor = s
			}

			editorPath, err := exec.LookPath(editor)

			if err != nil {
				return errors.Wrapf(err, "unable to determine path for editor %q", editor)

			}

			cmd := exec.Command(editorPath, tmpValuesFilePath)

			cmd.Stdin = os.Stdin
			cmd.Stdout = os.Stdout
			cmd.Stderr = os.Stderr

			err = cmd.Start()

			if err != nil {
				return errors.Wrapf(err, "cannot execute editor on configuration")
			}

			err = cmd.Wait()

			if err != nil {
				return errors.Wrapf(err, "editing of values configuration failed")
			}

			_, err = config.NewInstallationConfigFromFile(tmpValuesFilePath)

			if err != nil {
				return errors.Wrapf(err, "error in values configuration file")
			}

			err = os.Rename(tmpValuesFilePath, valuesFilePath)

			if err != nil {
				return errors.Wrapf(err, "unable to update default configuration")
			}

			return nil
		},
	}

	return c
}
