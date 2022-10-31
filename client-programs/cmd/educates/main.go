/*
Copyright © 2022 The Educates Authors.
*/
package main

import (
	"os"

	"github.com/spf13/cobra"
	"github.com/vmware-tanzu-labs/educates-training-platform/client-programs/pkg/cmd"
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
			Message: "Workshop Commands (Docker):",
			Commands: []*cobra.Command{
				cmd.NewDockerCmd(),
			},
		},
		{
			Message: "Workshop Commands (Kubernetes):",
			Commands: []*cobra.Command{
				cmd.NewWorkshopDeployCmd(),
				cmd.NewWorkshopUpdateCmd(),
				cmd.NewWorkshopDeleteCmd(),
				cmd.NewWorkshopsListCmd(),
			},
		},
		{
			Message: "Portal Commands (Kubernetes):",
			Commands: []*cobra.Command{
				cmd.NewPortalsListCmd(),
				cmd.NewPortalOpenCmd(),
				cmd.NewPortalCreateCmd(),
				cmd.NewPortalDeleteCmd(),
				cmd.NewPortalPasswordCmd(),
			},
		},
		{
			Message: "Content Commands (Host):",
			Commands: []*cobra.Command{
				cmd.NewTemplatesListCmd(),
				cmd.NewWorkshopNewCmd(),
				cmd.NewFilesPublishCmd(),
			},
		},
		{
			Message: "Management Commands (Host):",
			Commands: []*cobra.Command{
				cmd.NewClusterCmd(),
				cmd.NewRegistryCmd(),
				cmd.NewResolverCmd(),
			},
		},
		{
			Message: "Installation Commands (Kubernetes):",
			Commands: []*cobra.Command{
				cmd.NewServicesCmd(),
				cmd.NewOperatorsCmd(),
			},
		},
		{
			Message: "Configuration Commands:",
			Commands: []*cobra.Command{
				cmd.NewConfigCmd(),
				cmd.NewSecretsCmd(),
			},
		},
		{
			Message: "Documentation Commands:",
			Commands: []*cobra.Command{
				cmd.NewVersionCmd(),
				cmd.NewDocsCmd(),
			},
		},
	}

	commandGroups.Add(rootCmd)

	templates.ActsAsRootCommand(rootCmd, []string{"options"}, commandGroups...)
}

func main() {
	Execute()
}
