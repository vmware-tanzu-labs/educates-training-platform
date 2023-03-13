// Copyright 2022-2023 The Educates Authors.

package resolver

import (
	"bytes"
	"context"
	"fmt"
	"html/template"
	"io"
	"os"
	"path"
	"time"

	"github.com/adrg/xdg"
	"github.com/docker/docker/api/types"
	"github.com/docker/docker/api/types/container"
	"github.com/docker/docker/api/types/mount"
	"github.com/docker/docker/client"
	"github.com/docker/go-connections/nat"
	"github.com/pkg/errors"
	"github.com/vmware-tanzu-labs/educates-training-platform/client-programs/pkg/config"
)

const dnsmasqConfigTemplateData = `
#log-queries
no-resolv
server=1.0.0.1
server=1.1.1.1
strict-order

address=/{{.IngressDomain}}/{{.HostIPAddress}}
`

func DeployResolver(domain string) error {
	ctx := context.Background()

	fmt.Println("Deploying local DNS resolver")

	cli, err := client.NewClientWithOpts(client.FromEnv)

	if err != nil {
		return errors.Wrap(err, "unable to create docker client")
	}

	_, err = cli.ContainerInspect(ctx, "educates-resolver")

	if err == nil {
		// If we can retrieve a container of required name we assume it is
		// running okay. Technically it could be restarting, stopping or
		// have exited and container was not removed, but if that is the case
		// then leave it up to the user to sort out.

		return nil
	}

	reader, err := cli.ImagePull(ctx, "docker.io/jpillora/dnsmasq:latest", types.ImagePullOptions{})
	if err != nil {
		return errors.Wrap(err, "cannot pull dnsmasq image")
	}

	defer reader.Close()
	io.Copy(os.Stdout, reader)

	dnsmasqConfigTemplate, err := template.New("dnsmasq-config").Parse(dnsmasqConfigTemplateData)

	if err != nil {
		return errors.Wrap(err, "failed to parse dnsmasq config template")
	}

	var clusterConfigData bytes.Buffer

	localIPAddress, err := config.HostIP()

	if err != nil {
		localIPAddress = "127.0.0.1"
	}

	config := map[string]string{
		"IngressDomain": domain,
		"HostIPAddress": localIPAddress,
	}

	err = dnsmasqConfigTemplate.Execute(&clusterConfigData, config)

	if err != nil {
		return errors.Wrap(err, "failed to generate dnsmasq config")
	}

	configFileDir := path.Join(xdg.DataHome, "educates")
	configFileName := path.Join(configFileDir, "dnsmasq.conf")

	_ = os.Mkdir(configFileDir, os.ModePerm)

	err = os.WriteFile(configFileName, clusterConfigData.Bytes(), 0644)

	if err != nil {
		return errors.Wrap(err, "failed to write dnsmasq config")
	}

	hostConfig := &container.HostConfig{
		PortBindings: nat.PortMap{
			"53/udp": []nat.PortBinding{
				{
					HostIP:   "127.0.0.1",
					HostPort: "53",
				},
			},
		},
		Mounts: []mount.Mount{
			{
				Type:     "bind",
				Source:   configFileName,
				Target:   "/etc/dnsmasq.conf",
				ReadOnly: true,
			},
		},
		RestartPolicy: container.RestartPolicy{
			Name: "always",
		},
		LogConfig: container.LogConfig{
			Config: map[string]string{
				"max-size": "100m",
			},
		},
	}

	resp, err := cli.ContainerCreate(ctx, &container.Config{
		Image: "docker.io/jpillora/dnsmasq:latest",
		Tty:   false,
		ExposedPorts: nat.PortSet{
			"53/udp": struct{}{},
		},
	}, hostConfig, nil, nil, "educates-resolver")

	if err != nil {
		return errors.Wrap(err, "cannot create resolver container")
	}

	if err := cli.ContainerStart(ctx, resp.ID, types.ContainerStartOptions{}); err != nil {
		return errors.Wrap(err, "unable to start resolver")
	}

	return nil
}

func DeleteResolver() error {
	ctx := context.Background()

	fmt.Println("Deleting local DNS resolver")

	cli, err := client.NewClientWithOpts(client.FromEnv)

	if err != nil {
		return errors.Wrap(err, "unable to create docker client")
	}

	_, err = cli.ContainerInspect(ctx, "educates-resolver")

	if err != nil {
		// If we can't retrieve a container of required name we assume it does
		// not actually exist.

		return nil
	}

	timeout := time.Duration(30) * time.Second

	err = cli.ContainerStop(ctx, "educates-resolver", &timeout)

	if err != nil {
		return errors.Wrap(err, "unable to stop DNS resolver container")
	}

	err = cli.ContainerRemove(ctx, "educates-resolver", types.ContainerRemoveOptions{})

	if err != nil {
		return errors.Wrap(err, "unable to delete DNS resolver container")
	}

	return nil
}
