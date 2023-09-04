package cmd

import (
	"context"
	"fmt"
	"io"
	"os"
	"os/exec"
	"path"
	"sync"
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
			dockerWorkshopsManager := NewDockerWorkshopsManager()

			workshops, err := dockerWorkshopsManager.ListWorkhops()

			if err != nil {
				return errors.Wrap(err, "cannot display list of workshops")
			}

			w := new(tabwriter.Writer)
			w.Init(os.Stdout, 8, 8, 3, ' ', 0)

			defer w.Flush()

			fmt.Fprintf(w, "%s\t%s\t%s\n%s\n", "NAME", "URL", "SOURCE", "STATUS")

			for _, workshop := range workshops {
				fmt.Fprintf(w, "%s\t%s\t%s\n%s\n", workshop.Session, workshop.Url, workshop.Source, workshop.Status)
			}

			return nil
		},
	}

	return c
}

type DockerWorkshopsManager struct {
	Statuses      map[string]string
	StatusesMutex sync.Mutex
}

func NewDockerWorkshopsManager() DockerWorkshopsManager {
	return DockerWorkshopsManager{
		Statuses:      map[string]string{},
		StatusesMutex: sync.Mutex{},
	}
}

type DockerWorkshopDetails struct {
	Session string `json:"session"`
	Url     string `json:"url,omitempty"`
	Source  string `json:"source,omitempty"`
	Status  string `json:"status"`
}

func (m *DockerWorkshopsManager) SetStatus(name string, status string) {
	m.StatusesMutex.Lock()
	m.Statuses[name] = status
	m.StatusesMutex.Unlock()
}

func (m *DockerWorkshopsManager) ClearStatus(name string) {
	delete(m.Statuses, name)
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

	m.StatusesMutex.Lock()

	defer m.StatusesMutex.Unlock()

	for _, container := range containers {
		url, found := container.Labels["training.educates.dev/url"]
		source := container.Labels["training.educates.dev/source"]
		instance := container.Labels["training.educates.dev/session"]

		status, statusFound := m.Statuses[instance]

		if !statusFound {
			status = "Running"
		}

		if found && url != "" && len(container.Names) != 0 {
			workshops = append(workshops, DockerWorkshopDetails{
				Session: instance,
				Url:     url,
				Source:  source,
				Status:  status,
			})
		}
	}

	return workshops, nil
}

func (m *DockerWorkshopsManager) DeleteWorkshop(name string, stdout io.Writer, stderr io.Writer) error {
	m.SetStatus(name, "Stopping")

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

	defer m.ClearStatus(name)

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
