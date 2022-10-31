// Copyright 2022 The Educates Authors.

package cmd

import (
	"fmt"

	"github.com/pkg/errors"
	"github.com/spf13/cobra"
)

func NewTemplatesListCmd() *cobra.Command {
	var c = &cobra.Command{
		Args:  cobra.NoArgs,
		Use:   "list-templates",
		Short: "List available workshop templates",
		RunE: func(_ *cobra.Command, _ []string) error {
			files, err := workshopTemplates.ReadDir("templates")

			if err != nil {
				return errors.Wrap(err, "unable to read embedded templates")
			}

			for _, file := range files {
				fmt.Println(file.Name())
			}

			return nil
		},
	}

	return c
}
