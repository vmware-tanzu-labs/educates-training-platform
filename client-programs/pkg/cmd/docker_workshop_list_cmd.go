// Copyright 2022 The Educates Authors.

package cmd

import (
	"context"
	"fmt"
	"os"
	"text/tabwriter"

	"github.com/docker/docker/api/types"
	"github.com/docker/docker/client"
	"github.com/pkg/errors"
	"github.com/spf13/cobra"
)

func (p *ProjectInfo) NewDockerWorkshopListCmd() *cobra.Command {
	var c = &cobra.Command{
		Args:  cobra.NoArgs,
		Use:   "list",
		Short: "List workshops deployed to Docker",
		RunE: func(_ *cobra.Command, _ []string) error {
			ctx := context.Background()

			cli, err := client.NewClientWithOpts(client.FromEnv)

			if err != nil {
				return errors.Wrap(err, "unable to create docker client")
			}

			containers, err := cli.ContainerList(ctx, types.ContainerListOptions{})

			if err != nil {
				return errors.Wrap(err, "unable to list containers")
			}

			w := new(tabwriter.Writer)
			w.Init(os.Stdout, 8, 8, 3, ' ', 0)

			defer w.Flush()

			fmt.Fprintf(w, "%s\t%s\t%s\n", "NAME", "URL", "SOURCE")

			for _, container := range containers {
				url, found := container.Labels["training.educates.dev/url"]
				source := container.Labels["training.educates.dev/source"]
				instance := container.Labels["training.educates.dev/session"]

				if found && url != "" && len(container.Names) != 0 {
					fmt.Fprintf(w, "%s\t%s\t%s\n", instance, url, source)
				}
			}

			return nil
		},
	}

	return c
}
