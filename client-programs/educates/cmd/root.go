/*
Copyright © 2022 The Educates Authors.
*/
package cmd

import (
	"os"
	"strings"

	_ "embed"

	"github.com/spf13/cobra"
	"k8s.io/kubectl/pkg/util/templates"
)

//go:embed version.txt
var clientVersionData string

var ClientVersion = strings.TrimSpace(clientVersionData)

var rootCmd = &cobra.Command{
	Use:   "educates",
	Short: "Tool for managing Educates",
}

func Execute() {
	err := rootCmd.Execute()
	if err != nil {
		os.Exit(1)
	}
}

func init() {
	commandGroups := templates.CommandGroups{
		{
			Message: "Workshop Commands:",
			Commands: []*cobra.Command{
				NewWorkshopDeployCmd(),
				NewWorkshopUpdateCmd(),
				NewWorkshopDeleteCmd(),
				NewWorkshopsListCmd(),
			},
		},
		{
			Message: "Portal Commands:",
			Commands: []*cobra.Command{
				NewPortalOpenCmd(),
				NewPortalsListCmd(),
				NewPortalCredentialsCmd(),
			},
		},
		{
			Message: "Environment Commands:",
			Commands: []*cobra.Command{
				NewClusterCmd(),
				NewRegistryCmd(),
				NewResolverCmd(),
			},
		},
		{
			Message: "Installation Commands:",
			Commands: []*cobra.Command{
				NewServicesCmd(),
				NewOperatorsCmd(),
			},
		},
		{
			Message: "Configuration Commands:",
			Commands: []*cobra.Command{
				NewConfigCmd(),
				NewSecretsCmd(),
			},
		},
		{
			Message: "Documentation Commands:",
			Commands: []*cobra.Command{
				NewDocsCmd(),
			},
		},
	}

	commandGroups.Add(rootCmd)
	templates.ActsAsRootCommand(rootCmd, []string{"options"}, commandGroups...)
}
