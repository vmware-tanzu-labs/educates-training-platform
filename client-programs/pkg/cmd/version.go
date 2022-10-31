/*
Copyright © 2022 The Educates Authors.
*/
package cmd

import (
	"fmt"
	"strings"

	"github.com/spf13/cobra"
)

func NewVersionCmd() *cobra.Command {
	var c = &cobra.Command{
		Args:  cobra.NoArgs,
		Use:   "version",
		Short: "Display the version of Educates",
		RunE: func(_ *cobra.Command, _ []string) error {
			fmt.Println(strings.TrimSpace(clientVersionData))
			return nil
		},
	}

	return c
}
