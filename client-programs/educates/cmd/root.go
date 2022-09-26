/*
Copyright © 2022 The Educates Authors.
*/
package cmd

import (
	"os"

	"github.com/spf13/cobra"
	"k8s.io/kubectl/pkg/util/templates"
)

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
			Message: "Available Commands:",
			Commands: []*cobra.Command{
				NewClusterCreateCmd(),
				NewClusterDeleteCmd(),
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
		{
			Message: "Management Commands:",
			Commands: []*cobra.Command{
				NewClusterCmd(),
				NewOperatorsCmd(),
				NewRegistryCmd(),
				NewResolverCmd(),
				NewServicesCmd(),
			},
		},
	}

	commandGroups.Add(rootCmd)
	templates.ActsAsRootCommand(rootCmd, []string{"options"}, commandGroups...)
}
