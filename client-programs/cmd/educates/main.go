// Copyright 2022 The Educates Authors.

package main

import (
	"os"
	"strings"

	"github.com/spf13/cobra"
	"github.com/vmware-tanzu-labs/educates-training-platform/client-programs/pkg/cmd"
	"k8s.io/kubectl/pkg/util/templates"
)

// Version of the Educates package which will be installed by the CLI. This is
// overridden with the actual version at build time when making a release.
var projectVersion string = "develop"

func main() {
	project := cmd.NewProjectInfo(strings.TrimSpace(projectVersion))

	rootCmd := &cobra.Command{
		Use:   "educates",
		Short: "Tool for managing Educates",
	}

	commandGroups := templates.CommandGroups{
		{
			Message: "Workshop Commands (Docker):",
			Commands: []*cobra.Command{
				project.NewDockerCmd(),
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
				project.NewClusterCmd(),
				cmd.NewRegistryCmd(),
				cmd.NewResolverCmd(),
			},
		},
		{
			Message: "Installation Commands (Kubernetes):",
			Commands: []*cobra.Command{
				project.NewServicesCmd(),
				project.NewOperatorsCmd(),
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
				project.NewVersionCmd(),
				cmd.NewDocsCmd(),
			},
		},
	}

	commandGroups.Add(rootCmd)

	templates.ActsAsRootCommand(rootCmd, []string{"options"}, commandGroups...)

	err := rootCmd.Execute()

	if err != nil {
		os.Exit(1)
	}
}
