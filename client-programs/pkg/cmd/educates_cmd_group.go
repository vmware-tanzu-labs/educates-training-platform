// Copyright 2022 The Educates Authors.

package cmd

import (
	"github.com/spf13/cobra"
	"k8s.io/kubectl/pkg/util/templates"
)

/*
Create root Cobra command group for Educates CLI .
*/
func (p *ProjectInfo) NewEducatesCmdGroup() *cobra.Command {
	c := &cobra.Command{
		Use:   "educates",
		Short: "Tool for managing Educates",
	}

	// Use command groups so can break up different commands into categories.
	// This also allows us to dictate the order in which they are displayed in
	// the help message, as otherwise they are displayed in sort order.

	commandGroups := templates.CommandGroups{
		{
			Message: "Workshop Commands (Docker):",
			Commands: []*cobra.Command{
				p.NewDockerCmd(),
			},
		},
		{
			Message: "Workshop Commands (Kubernetes):",
			Commands: []*cobra.Command{
				p.NewKubernetesWorkshopDeployCmd(),
				p.NewKubernetesWorkshopUpdateCmd(),
				p.NewKubernetesWorkshopDeleteCmd(),
				p.NewKubernetesWorkshopsListCmd(),
			},
		},
		{
			Message: "Portal Commands (Kubernetes):",
			Commands: []*cobra.Command{
				p.NewKubernetesPortalsListCmd(),
				p.NewKubernetesPortalOpenCmd(),
				p.NewKubernetesPortalCreateCmd(),
				p.NewKubernetesPortalDeleteCmd(),
				p.NewKubernetesPortalPasswordCmd(),
			},
		},
		{
			Message: "Content Commands (Host):",
			Commands: []*cobra.Command{
				p.NewTemplatesListCmd(),
				p.NewWorkshopNewCmd(),
				p.NewFilesPublishCmd(),
			},
		},
		{
			Message: "Management Commands (Host):",
			Commands: []*cobra.Command{
				p.NewClusterCmdGroup(),
				p.NewRegistryCmdGroup(),
				p.NewResolverCmdGroup(),
			},
		},
		{
			Message: "Installation Commands (Kubernetes):",
			Commands: []*cobra.Command{
				p.NewServicesCmdGroup(),
				p.NewOperatorsCmdGroup(),
			},
		},
		{
			Message: "Configuration Commands:",
			Commands: []*cobra.Command{
				p.NewConfigCmdGroup(),
				p.NewSecretsCmdGroup(),
			},
		},
		{
			Message: "Documentation Commands:",
			Commands: []*cobra.Command{
				p.NewProjectVersionCmd(),
				p.NewDocsCmdGroup(),
			},
		},
	}

	commandGroups.Add(c)

	templates.ActsAsRootCommand(c, []string{"options"}, commandGroups...)

	return c
}
