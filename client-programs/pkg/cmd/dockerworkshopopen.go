// Copyright 2022 The Educates Authors.

package cmd

import (
	"context"
	"fmt"
	"io"
	"net/http"
	"os/exec"
	"runtime"
	"time"

	"github.com/docker/docker/client"
	"github.com/pkg/errors"
	"github.com/spf13/cobra"
	"k8s.io/apimachinery/pkg/apis/meta/v1/unstructured"
)

type DockerWorkshopOpenOptions struct {
	Name string
	Path string
}

func (o *DockerWorkshopOpenOptions) Run() error {
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

	container, err := cli.ContainerInspect(ctx, name)

	if err != nil {
		return errors.New("unable to find workshop")
	}

	url, found := container.Config.Labels["training.educates.dev/url"]

	if !found || url == "" {
		return errors.New("can't determine URL for workshop")
	}

	// XXX Need a better way of handling very long startup times for container
	// due to workshop content or package downloads.

	for i := 1; i < 120; i++ {
		time.Sleep(time.Second)

		resp, err := http.Get(url)

		if err != nil {
			continue
		}

		defer resp.Body.Close()
		_, err = io.ReadAll(resp.Body)

		break
	}

	switch runtime.GOOS {
	case "linux":
		err = exec.Command("xdg-open", url).Start()
	case "windows":
		err = exec.Command("rundll32", "url.dll,FileProtocolHandler", url).Start()
	case "darwin":
		err = exec.Command("open", url).Start()
	default:
		err = fmt.Errorf("unsupported platform")
	}

	if err != nil {
		return errors.Wrap(err, "unable to open web browser")
	}

	return nil
}

func NewDockerWorkshopOpenCmd() *cobra.Command {
	var o DockerWorkshopOpenOptions

	var c = &cobra.Command{
		Args:  cobra.NoArgs,
		Use:   "open-workshop",
		Short: "Open workshop in browser",
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
