// Copyright 2022 The Educates Authors.

package cmd

import (
	"context"
	"fmt"
	"os"
	"os/exec"
	"path"

	"github.com/adrg/xdg"
	"github.com/docker/docker/client"
	"github.com/pkg/errors"
	"github.com/spf13/cobra"
	"k8s.io/apimachinery/pkg/apis/meta/v1/unstructured"
)

type DockerWorkshopDeleteOptions struct {
	Name string
	Path string
}

func (o *DockerWorkshopDeleteOptions) Run(cmd *cobra.Command) error {
	var err error

	var name = o.Name

	if name == "" {
		var path = o.Path

		// If path not provided assume the current working directory. When loading
		// the workshop will then expect the workshop definition to reside in the
		// resources/workshop.yaml file under the directory, the same as if a
		// directory path was provided explicitly.

		if path == "" {
			path = "."
		}

		// Load the workshop definition. The path can be a HTTP/HTTPS URL for a
		// local file system path for a directory or file.

		var workshop *unstructured.Unstructured

		if workshop, err = loadWorkshopDefinition(o.Name, path, "educates-cli"); err != nil {
			return err
		}

		name = workshop.GetName()
	}

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

	dockerCommand.Stdout = cmd.OutOrStdout()
	dockerCommand.Stderr = cmd.OutOrStderr()

	err = dockerCommand.Run()

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

func (p *ProjectInfo) NewDockerWorkshopDeleteCmd() *cobra.Command {
	var o DockerWorkshopDeleteOptions

	var c = &cobra.Command{
		Args:  cobra.NoArgs,
		Use:   "delete",
		Short: "Delete workshop from Docker",
		RunE:  func(cmd *cobra.Command, _ []string) error { return o.Run(cmd) },
	}

	c.Flags().StringVarP(
		&o.Name,
		"name",
		"n",
		"",
		"name to be used for the workshop definition, generated if not set",
	)
	c.Flags().StringVarP(
		&o.Path,
		"file",
		"f",
		".",
		"path to local workshop directory, definition file, or URL for workshop definition file",
	)

	return c
}
