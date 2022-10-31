// Copyright 2022 The Educates Authors.

package cmd

import (
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
		RunE: func(cmd *cobra.Command, _ []string) error {
			cmd.Println(ClientVersion)
			return nil
		},
	}

	return c
}
