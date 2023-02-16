// Copyright 2022-2023 The Educates Authors.

package cmd

import (
	"strings"

	"github.com/spf13/cobra"
	"k8s.io/kubectl/pkg/util/templates"
)

/*
Create root Cobra command group for Educates CLI .
*/
func (p *ProjectInfo) NewEducatesCmdGroup() *cobra.Command {
	c := &cobra.Command{
		Use:   "educates",
		Short: "Tools for managing Educates",
	}

	// Use a command group as it allows us to dictate the order in which they
	// are displayed in the help message, as otherwise they are displayed in
	// sort order.

	overrideCommandName := func(c *cobra.Command, name string) *cobra.Command {
		c.Use = strings.Replace(c.Use, c.Name(), name, 1)
		return c
	}

	commandGroups := templates.CommandGroups{
		{
			Message: "Cluster Commands (Aliases):",
			Commands: []*cobra.Command{
				overrideCommandName(p.NewAdminClusterCreateCmd(), "create-cluster"),
				overrideCommandName(p.NewAdminClusterDeleteCmd(), "delete-cluster"),
			},
		},
		{
			Message: "Workshop Commands (Aliases):",
			Commands: []*cobra.Command{
				overrideCommandName(p.NewWorkshopNewCmd(), "new-workshop"),
				overrideCommandName(p.NewWorkshopPublishCmd(), "publish-workshop"),
				overrideCommandName(p.NewClusterWorkshopDeployCmd(), "deploy-workshop"),
				overrideCommandName(p.NewClusterWorkshopListCmd(), "list-workshops"),
				overrideCommandName(p.NewClusterWorkshopUpdateCmd(), "update-workshop"),
				overrideCommandName(p.NewClusterWorkshopDeleteCmd(), "delete-workshop"),
				overrideCommandName(p.NewClusterPortalOpenCmd(), "browse-workshops"),
				overrideCommandName(p.NewClusterPortalPasswordCmd(), "view-credentials"),
			},
		},
		{
			Message: "Command Groups:",
			Commands: []*cobra.Command{
				p.NewProjectCmdGroup(),
				p.NewWorkshopCmdGroup(),
				p.NewTemplateCmdGroup(),
				p.NewClusterCmdGroup(),
				p.NewDockerCmdGroup(),
				p.NewAdminCmdGroup(),
			},
		},
	}

	commandGroups.Add(c)

	templates.ActsAsRootCommand(c, []string{"options"}, commandGroups...)

	return c
}
