// Copyright 2022 The Educates Authors.

package cmd

import (
	"os/exec"

	"github.com/pkg/errors"
	"github.com/spf13/cobra"
	"k8s.io/apimachinery/pkg/apis/meta/v1/unstructured"
)

type DockerWorkshopLogsOptions struct {
	Name   string
	Path   string
	Follow bool
}

func (o *DockerWorkshopLogsOptions) Run(cmd *cobra.Command) error {
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

	commandArgs := []string{
		"compose",
		"--project-name",
		name,
		"logs",
	}

	if o.Follow {
		commandArgs = append(commandArgs, "--follow")
	}

	dockerCommand := exec.Command("docker", commandArgs...)

	dockerCommand.Stdout = cmd.OutOrStdout()
	dockerCommand.Stderr = cmd.OutOrStderr()

	err = dockerCommand.Run()

	if err != nil {
		return errors.Wrap(err, "unable to obtain logs for workshop")
	}

	return nil
}

func (p *ProjectInfo) NewDockerWorkshopLogsCmd() *cobra.Command {
	var o DockerWorkshopLogsOptions

	var c = &cobra.Command{
		Args:  cobra.NoArgs,
		Use:   "logs",
		Short: "Display logs for workshop",
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
	c.Flags().BoolVar(
		&o.Follow,
		"follow",
		false,
		"specify if the logs should be streamed",
	)

	return c
}
