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
	"path"
	"path/filepath"
	"runtime"
	"strings"
	"time"

	"github.com/adrg/xdg"
	"github.com/docker/docker/api/types"
	"github.com/docker/docker/api/types/container"
	"github.com/docker/docker/api/types/mount"
	"github.com/docker/docker/client"
	"github.com/docker/go-connections/nat"
	"github.com/pkg/errors"
	"github.com/spf13/cobra"
	"gopkg.in/yaml.v2"
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

	// If path not provided assume the current working directory. When loading
	// the workshop will then expect the workshop definition to reside in the
	// resources/workshop.yaml file under the directory, the same as if a
	// directory path was provided explicitly.

	if o.Path == "" {
		o.Path = "."
	}

	// Load the workshop definition. The path can be a HTTP/HTTPS URL for a
	// local file system path for a directory or file.

	var workshop *unstructured.Unstructured

	if workshop, err = loadWorkshopDefinition("", o.Path, "educates-cli"); err != nil {
		return err
	}

	// Check that port to be used for the workshop is available.

	portAvailable, err := checkPortAvailability("127.0.0.1", []uint{o.Port})

	if err != nil || !portAvailable {
		return errors.Wrapf(err, "port %d not available for workshop", o.Port)
	}

	name := workshop.GetName()

	originalName := workshop.GetAnnotations()["training.educates.dev/workshop"]

	ctx := context.Background()

	cli, err := client.NewClientWithOpts(client.FromEnv)

	if err != nil {
		return errors.Wrap(err, "unable to create docker client")
	}

	_, err = cli.ContainerInspect(ctx, name)

	if err == nil {
		return errors.New("this workshop is already running")
	}

	registryInfo, err := cli.ContainerInspect(ctx, "educates-registry")

	if err != nil {
		return errors.Wrapf(err, "unable to inspect container for registry")
	}

	bridgeNetwork, exists := registryInfo.NetworkSettings.Networks["bridge"]

	if !exists {
		return errors.New("registry is not attached to bridge network")
	}

	configFileDir := path.Join(xdg.DataHome, "educates")
	workshopConfigDir := path.Join(configFileDir, "workshops", name)

	err = os.MkdirAll(workshopConfigDir, os.ModePerm)

	if err != nil {
		return errors.Wrapf(err, "unable to create workshops config directory")
	}

	applicationsConfig, _, _ := unstructured.NestedMap(workshop.Object, "spec", "session", "applications")
	ingressesConfig, _, _ := unstructured.NestedSlice(workshop.Object, "spec", "session", "ingresses")
	dashboardsConfig, _, _ := unstructured.NestedSlice(workshop.Object, "spec", "session", "dashboards")

	workshopConfig := map[string]interface{}{
		"spec": map[string]interface{}{
			"session": map[string]interface{}{
				"applications": applicationsConfig,
				"ingresses":    ingressesConfig,
				"dashboards":   dashboardsConfig,
			},
		},
	}

	workshopConfigData, err := yaml.Marshal(&workshopConfig)

	if err != nil {
		return errors.Wrap(err, "failed to generate workshop config")
	}

	workshopConfigFilePath := path.Join(workshopConfigDir, "workshop.yaml")

	workshopConfigFile, err := os.OpenFile(workshopConfigFilePath, os.O_RDWR|os.O_CREATE|os.O_TRUNC, os.ModePerm)

	if err != nil {
		return errors.Wrapf(err, "unable to create workshop config file %s", workshopConfigFilePath)
	}

	_, err = workshopConfigFile.Write(workshopConfigData)

	if err := workshopConfigFile.Close(); err != nil {
		return errors.Wrapf(err, "unable to close workshop config file %s", workshopConfigFilePath)
	}

	filesMounts := []mount.Mount{
		{
			Type:     "bind",
			Source:   workshopConfigFilePath,
			Target:   "/opt/eduk8s/config/workshop.yaml",
			ReadOnly: true,
		},
	}

	filesItems, found, _ := unstructured.NestedSlice(workshop.Object, "spec", "workshop", "files")

	if found && len(filesItems) != 0 {
		for idx, filesItem := range filesItems {
			directoriesConfig := []map[string]interface{}{}

			tmpPath, found := filesItem.(map[string]interface{})["path"]

			var filesItemPath string

			if found {
				filesItemPath = tmpPath.(string)
			} else {
				filesItemPath = "."
			}

			filesItemPath = filepath.Clean(path.Join("/opt/assets/files", filesItemPath))

			filesItem.(map[string]interface{})["path"] = "."

			directoriesConfig = append(directoriesConfig, map[string]interface{}{
				"path":     filesItemPath,
				"contents": []interface{}{filesItem},
			})

			vendirConfig := map[string]interface{}{
				"apiVersion":  "vendir.k14s.io/v1alpha1",
				"kind":        "Config",
				"directories": directoriesConfig,
			}

			vendirConfigData, err := yaml.Marshal(&vendirConfig)

			if err != nil {
				return errors.Wrap(err, "failed to generate vendir config")
			}

			tmpVendirConfigData := string(vendirConfigData)

			tmpVendirConfigData = strings.ReplaceAll(tmpVendirConfigData, "$(image_repository)", o.Repository)
			tmpVendirConfigData = strings.ReplaceAll(tmpVendirConfigData, "$(workshop_name)", originalName)

			vendirConfigData = []byte(tmpVendirConfigData)

			vendirConfigFilePath := path.Join(workshopConfigDir, fmt.Sprintf("vendir-assets-%02d.yaml", idx+1))

			vendirConfigFile, err := os.OpenFile(vendirConfigFilePath, os.O_RDWR|os.O_CREATE|os.O_TRUNC, os.ModePerm)

			if err != nil {
				return errors.Wrapf(err, "unable to create workshop files vendir file %s", vendirConfigFilePath)
			}

			_, err = vendirConfigFile.Write(vendirConfigData)

			if err := vendirConfigFile.Close(); err != nil {
				return errors.Wrapf(err, "unable to close workshop files vendir file %s", vendirConfigFilePath)
			}

			filesMounts = append(filesMounts, mount.Mount{
				Type:     "bind",
				Source:   vendirConfigFilePath,
				Target:   fmt.Sprintf("/opt/eduk8s/config/vendir-assets-%02d.yaml", idx+1),
				ReadOnly: true,
			})
		}
	}

	packagesItems, found, _ := unstructured.NestedSlice(workshop.Object, "spec", "workshop", "packages")

	if found && len(packagesItems) != 0 {
		directoriesConfig := []map[string]interface{}{}

		for _, packagesItem := range packagesItems {
			tmpPackagesItem := packagesItem.(map[string]interface{})

			tmpName, found := tmpPackagesItem["name"]

			if !found {
				continue
			}

			packagesItemPath := filepath.Clean(path.Join("/opt/packages", tmpName.(string)))

			tmpPackagesFilesItem := tmpPackagesItem["files"]

			packagesFilesItem := tmpPackagesFilesItem.([]interface{})

			for _, tmpEntry := range packagesFilesItem {
				entry := tmpEntry.(map[string]interface{})

				_, found = entry["path"]

				if !found {
					entry["path"] = "."
				}
			}

			directoriesConfig = append(directoriesConfig, map[string]interface{}{
				"path":     packagesItemPath,
				"contents": packagesFilesItem,
			})

		}

		vendirConfig := map[string]interface{}{
			"apiVersion":  "vendir.k14s.io/v1alpha1",
			"kind":        "Config",
			"directories": directoriesConfig,
		}

		vendirConfigData, err := yaml.Marshal(&vendirConfig)

		if err != nil {
			return errors.Wrap(err, "failed to generate vendir config")
		}

		tmpVendirConfigData := string(vendirConfigData)

		tmpVendirConfigData = strings.ReplaceAll(tmpVendirConfigData, "$(image_repository)", o.Repository)
		tmpVendirConfigData = strings.ReplaceAll(tmpVendirConfigData, "$(workshop_name)", originalName)

		vendirConfigData = []byte(tmpVendirConfigData)

		vendirConfigFilePath := path.Join(workshopConfigDir, "vendir-packages.yaml")

		vendirConfigFile, err := os.OpenFile(vendirConfigFilePath, os.O_RDWR|os.O_CREATE|os.O_TRUNC, os.ModePerm)

		if err != nil {
			return errors.Wrapf(err, "unable to create workshop packages vendir file %s", vendirConfigFilePath)
		}

		_, err = vendirConfigFile.Write(vendirConfigData)

		if err := vendirConfigFile.Close(); err != nil {
			return errors.Wrapf(err, "unable to close workshop packages vendir file %s", vendirConfigFilePath)
		}

		filesMounts = append(filesMounts, mount.Mount{
			Type:     "bind",
			Source:   vendirConfigFilePath,
			Target:   "/opt/eduk8s/config/vendir-packages.yaml",
			ReadOnly: true,
		})
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
		Mounts:     filesMounts,
		AutoRemove: true,
		ExtraHosts: []string{
			fmt.Sprintf("registry.docker.local:%s", bridgeNetwork.IPAddress),
		},
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
			fmt.Sprintf("IMAGE_REPOSITORY=%s", o.Repository),
		},
	}, hostConfig, nil, nil, name)

	if err != nil {
		return errors.Wrap(err, "cannot create workshop container")
	}

	if err := cli.ContainerStart(ctx, resp.ID, types.ContainerStartOptions{}); err != nil {
		return errors.Wrap(err, "unable to start workshop")
	}

	// XXX Need a better way of handling very long startup times for container
	// due to workshop content or package downloads.

	if !o.DisableOpenBrowser {
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
		"registry.docker.local:5000",
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
