package cmd

import (
	"context"
	"fmt"
	"io"
	"os"
	"os/exec"
	"path"
	"text/tabwriter"

	"github.com/adrg/xdg"
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
			dockerWorkshopsManager := DockerWorkshopsManager{}

			workshops, err := dockerWorkshopsManager.ListWorkhops()

			if err != nil {
				return errors.Wrap(err, "cannot display list of workshops")
			}

			w := new(tabwriter.Writer)
			w.Init(os.Stdout, 8, 8, 3, ' ', 0)

			defer w.Flush()

			fmt.Fprintf(w, "%s\t%s\t%s\n", "NAME", "URL", "SOURCE")

			for _, workshop := range workshops {
				fmt.Fprintf(w, "%s\t%s\t%s\n", workshop.Session, workshop.Url, workshop.Source)
			}

			return nil
		},
	}

	return c
}

type DockerWorkshopsManager struct{}
type DockerWorkshopDetails struct {
	Session string `json:"session"`
	Url     string `json:"url"`
	Source  string `json:"source"`
	Status  string `json:"status"`
}

func (m *DockerWorkshopsManager) ListWorkhops() ([]DockerWorkshopDetails, error) {
	workshops := []DockerWorkshopDetails{}

	ctx := context.Background()

	cli, err := client.NewClientWithOpts(client.FromEnv)

	if err != nil {
		return nil, errors.Wrap(err, "unable to create docker client")
	}

	containers, err := cli.ContainerList(ctx, types.ContainerListOptions{})

	if err != nil {
		return nil, errors.Wrap(err, "unable to list containers")
	}

	for _, container := range containers {
		url, found := container.Labels["training.educates.dev/url"]
		source := container.Labels["training.educates.dev/source"]
		instance := container.Labels["training.educates.dev/session"]

		if found && url != "" && len(container.Names) != 0 {
			workshops = append(workshops, DockerWorkshopDetails{
				Session: instance,
				Url:     url,
				Source:  source,
			})
		}
	}

	return workshops, nil
}

func (m *DockerWorkshopsManager) DeleteWorkshop(name string, stdout io.Writer, stderr io.Writer) error {
	dockerCommand := exec.Command(
		"docker",
		"compose",
		"--project-name",
		name,
		"rm",
		"--stop",
		"--force",
		"--volumes",
	)

	dockerCommand.Stdout = stdout
	dockerCommand.Stderr = stderr

	err := dockerCommand.Run()

	if err != nil {
		return errors.Wrap(err, "unable to stop workshop")
	}

	ctx := context.Background()

	cli, err := client.NewClientWithOpts(client.FromEnv)

	if err != nil {
		return errors.Wrap(err, "unable to create docker client")
	}

	err = cli.VolumeRemove(ctx, fmt.Sprintf("%s_workshop", name), false)

	if err != nil {
		return errors.Wrap(err, "unable to delete workshop volume")
	}

	configFileDir := path.Join(xdg.DataHome, "educates")
	workshopConfigDir := path.Join(configFileDir, "workshops", name)
	composeConfigDir := path.Join(configFileDir, "compose", name)

	os.RemoveAll(workshopConfigDir)
	os.RemoveAll(composeConfigDir)

	return nil
}
