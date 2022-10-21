/*
Copyright © 2022 The Educates Authors.
*/
package cmd

import (
	"context"
	"fmt"
	"io"
	"net/http"
	"os"
	"os/exec"
	"runtime"
	"strings"
	"time"

	"github.com/docker/docker/api/types"
	"github.com/docker/docker/api/types/container"
	"github.com/docker/docker/client"
	"github.com/docker/go-connections/nat"
	"github.com/pkg/errors"
	"github.com/spf13/cobra"
	"k8s.io/apimachinery/pkg/apis/meta/v1/unstructured"
)

type DockerWorkshopDeployOptions struct {
	Path               string
	Port               uint
	Repository         string
	DisableOpenBrowser bool
}

func (o *DockerWorkshopDeployOptions) Run() error {
	var err error

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

	if workshop, err = loadWorkshopDefinition("", path, "educates-cli"); err != nil {
		return err
	}

	// Check that port to be used for the workshop is available.

	portAvailable, err := checkPortAvailability("127.0.0.1", []uint{o.Port})

	if err != nil || !portAvailable {
		return errors.Wrapf(err, "port %d not available for workshop", o.Port)
	}

	name := workshop.GetName()

	ctx := context.Background()

	cli, err := client.NewClientWithOpts(client.FromEnv)

	if err != nil {
		return errors.Wrap(err, "unable to create docker client")
	}

	_, err = cli.ContainerInspect(ctx, name)

	if err == nil {
		return errors.New("this workshop is already running")
	}

	image, found, err := unstructured.NestedString(workshop.Object, "spec", "workshop", "image")

	if err != nil {
		return errors.Wrapf(err, "unable to parse workshop definition")
	}

	if !found {
		image = fmt.Sprintf("ghcr.io/vmware-tanzu-labs/educates-base-environment:%s", strings.TrimSpace(clientVersionData))
	}

	image = strings.ReplaceAll(image, "$(image_repository)", o.Repository)

	reader, err := cli.ImagePull(ctx, image, types.ImagePullOptions{})
	if err != nil {
		return errors.Wrap(err, "cannot pull workshop base image")
	}

	defer reader.Close()
	io.Copy(os.Stdout, reader)

	hostConfig := &container.HostConfig{
		PortBindings: nat.PortMap{
			"10081/tcp": []nat.PortBinding{
				{
					HostIP:   "127.0.0.1",
					HostPort: fmt.Sprintf("%d", o.Port),
				},
			},
		},
		AutoRemove: true,
	}

	labels := workshop.GetAnnotations()

	url := fmt.Sprintf("http://workshop.127-0-0-1.nip.io:%d", o.Port)

	labels["training.educates.dev/url"] = url

	resp, err := cli.ContainerCreate(ctx, &container.Config{
		Image: image,
		Tty:   false,
		ExposedPorts: nat.PortSet{
			"10081/tcp": struct{}{},
		},
		Labels: labels,
		Env: []string{
			"INGRESS_PROTOCOL=http",
			"INGRESS_DOMAIN=127-0-0-1.nip.io",
			fmt.Sprintf("INGRESS_PORT_SUFFIX=:%d", o.Port),
			// fmt.Sprintf("SESSION_NAMESPACE=%s", name),
		},
	}, hostConfig, nil, nil, name)

	if err != nil {
		return errors.Wrap(err, "cannot create workshop container")
	}

	if err := cli.ContainerStart(ctx, resp.ID, types.ContainerStartOptions{}); err != nil {
		return errors.Wrap(err, "unable to start workshop")
	}

	if !o.DisableOpenBrowser {
		for i := 1; i < 30; i++ {
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
	}

	return nil
}

func NewDockerWorkshopDeployCmd() *cobra.Command {
	var o DockerWorkshopDeployOptions

	var c = &cobra.Command{
		Args:  cobra.NoArgs,
		Use:   "deploy-workshop",
		Short: "Deploy workshop to Docker",
		RunE:  func(_ *cobra.Command, _ []string) error { return o.Run() },
	}

	c.Flags().StringVarP(
		&o.Path,
		"file",
		"f",
		".",
		"path to local workshop directory, definition file, or URL for workshop definition file",
	)
	c.Flags().UintVarP(
		&o.Port,
		"port",
		"p",
		10081,
		"port to host the workshop on localhost",
	)
	c.Flags().StringVar(
		&o.Repository,
		"repository",
		"localhost:5001",
		"the address of the image repository",
	)
	c.Flags().BoolVar(
		&o.DisableOpenBrowser,
		"disable-open-browser ",
		false,
		"disable automatic launching of the browser",
	)

	return c
}
