/*
Copyright © 2022 The Educates Authors.
*/
package cmd

import (
	"fmt"
	"strings"

	_ "embed"

	"github.com/spf13/cobra"
)

//go:embed version.txt
var clientVersionData string

var ClientVersion = strings.TrimSpace(clientVersionData)

func NewVersionCmd() *cobra.Command {
	var c = &cobra.Command{
		Args:  cobra.NoArgs,
		Use:   "version",
		Short: "Display the version of Educates",
		RunE: func(_ *cobra.Command, _ []string) error {
			fmt.Println(ClientVersion)
			return nil
		},
	}

	return c
}
