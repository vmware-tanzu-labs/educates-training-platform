/*
Copyright © 2022 The Educates Authors.
*/
package cmd

import (
	"context"
	"os"
	"path"
	"time"

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

func (o *DockerWorkshopDeleteOptions) Run() error {
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

	ctx := context.Background()

	cli, err := client.NewClientWithOpts(client.FromEnv)

	if err != nil {
		return errors.Wrap(err, "unable to create docker client")
	}

	_, err = cli.ContainerInspect(ctx, name)

	if err == nil {
		timeout := time.Duration(30) * time.Second

		err = cli.ContainerStop(ctx, name, &timeout)

		if err != nil {
			return errors.Wrap(err, "unable to stop workshop container")
		}
	}

	configFileDir := path.Join(xdg.DataHome, "educates")
	workshopConfigDir := path.Join(configFileDir, "workshops")

	workshopConfigFilePath := path.Join(workshopConfigDir, name+"--config.yaml")

	os.Remove(workshopConfigFilePath)

	return nil
}

func NewDockerWorkshopDeleteCmd() *cobra.Command {
	var o DockerWorkshopDeleteOptions

	var c = &cobra.Command{
		Args:  cobra.NoArgs,
		Use:   "delete-workshop",
		Short: "Delete workshop from Docker",
		RunE:  func(_ *cobra.Command, _ []string) error { return o.Run() },
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
