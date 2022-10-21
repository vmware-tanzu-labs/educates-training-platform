/*
Copyright © 2022 The Educates Authors.
*/
package cmd

import (
	"context"
	"fmt"
	"os"
	"strings"
	"text/tabwriter"

	"github.com/docker/docker/api/types"
	"github.com/docker/docker/client"
	"github.com/pkg/errors"
	"github.com/spf13/cobra"
)

func NewDockerWorkshopsListCmd() *cobra.Command {
	var c = &cobra.Command{
		Args:  cobra.NoArgs,
		Use:   "list-workshops",
		Short: "Output list of workshops",
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
				source, _ := container.Labels["training.educates.dev/source"]

				if found && url != "" && len(container.Names) != 0 {
					name := strings.TrimLeft(container.Names[0], "/")
					fmt.Fprintf(w, "%s\t%s\t%s\n", name, url, source)
				}
			}

			return nil
		},
	}

	return c
}
