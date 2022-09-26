/*
Copyright © 2022 The Educates Authors.
*/
package registry

import (
	"context"
	"fmt"
	"io"
	"os"
	"time"

	"github.com/docker/docker/api/types"
	"github.com/docker/docker/api/types/container"
	"github.com/docker/docker/api/types/network"
	"github.com/docker/docker/client"
	"github.com/docker/go-connections/nat"
	"github.com/pkg/errors"
	apiv1 "k8s.io/api/core/v1"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/client-go/kubernetes"

	"github.com/vmware-tanzu-labs/educates-training-platform/client-programs/educates/pkg/config"
)

func DeployRegistry() error {
	ctx := context.Background()

	fmt.Println("Deploying local image registry")

	cli, err := client.NewClientWithOpts(client.FromEnv)

	if err != nil {
		return errors.Wrap(err, "unable to create docker client")
	}

	_, err = cli.ContainerInspect(ctx, "educates-registry")

	if err == nil {
		// If we can retrieve a container of required name we assume it is
		// running okay. Technically it could be restarting, stopping or
		// have exited and container was not removed, but if that is the case
		// then leave it up to the user to sort out.

		return nil
	}

	reader, err := cli.ImagePull(ctx, "docker.io/library/registry:2", types.ImagePullOptions{})
	if err != nil {
		return errors.Wrap(err, "cannot pull registry image")
	}

	defer reader.Close()
	io.Copy(os.Stdout, reader)

	hostConfig := &container.HostConfig{
		PortBindings: nat.PortMap{
			"5000/tcp": []nat.PortBinding{
				{
					HostIP:   "127.0.0.1",
					HostPort: "5001",
				},
			},
		},
		RestartPolicy: container.RestartPolicy{
			Name: "always",
		},
	}

	resp, err := cli.ContainerCreate(ctx, &container.Config{
		Image: "docker.io/library/registry:2",
		Tty:   false,
		ExposedPorts: nat.PortSet{
			"5000/tcp": struct{}{},
		},
	}, hostConfig, nil, nil, "educates-registry")

	if err != nil {
		return errors.Wrap(err, "cannot create registry container")
	}

	if err := cli.ContainerStart(ctx, resp.ID, types.ContainerStartOptions{}); err != nil {
		return errors.Wrap(err, "unable to start registry")
	}

	cli.NetworkDisconnect(ctx, "kind", "educates-registry", false)

	err = cli.NetworkConnect(ctx, "kind", "educates-registry", &network.EndpointSettings{})

	if err != nil {
		return errors.Wrap(err, "unable to connect registry to cluster network")
	}

	return nil
}

func DeleteRegistry() error {
	ctx := context.Background()

	fmt.Println("Deleting local image registry")

	cli, err := client.NewClientWithOpts(client.FromEnv)

	if err != nil {
		return errors.Wrap(err, "unable to create docker client")
	}

	_, err = cli.ContainerInspect(ctx, "educates-registry")

	if err != nil {
		// If we can't retrieve a container of required name we assume it does
		// not actually exist.

		return nil
	}

	timeout := time.Duration(10) * time.Second

	err = cli.ContainerStop(ctx, "educates-registry", &timeout)

	if err != nil {
		return errors.Wrap(err, "unable to stop registry container")
	}

	err = cli.ContainerRemove(ctx, "educates-registry", types.ContainerRemoveOptions{})

	if err != nil {
		return errors.Wrap(err, "unable to delete registry container")
	}

	return nil
}

func AddRegistryService(k8sclient *kubernetes.Clientset) error {
	ctx := context.Background()

	cli, err := client.NewClientWithOpts(client.FromEnv)

	if err != nil {
		return errors.Wrap(err, "unable to create docker client")
	}

	info, err := cli.Info(ctx)

	if err != nil {
		return errors.Wrap(err, "unable to query docker server details")
	}

	var service apiv1.Service

	if info.Name == "docker-desktop" {
		service = apiv1.Service{
			ObjectMeta: metav1.ObjectMeta{
				Name: "registry",
			},
			Spec: apiv1.ServiceSpec{
				Type:         apiv1.ServiceTypeExternalName,
				ExternalName: "host.docker.internal",
				Selector: map[string]string{
					"app": "registry",
				},
			},
		}
	} else {
		ipAddr, err := config.HostIP()

		if err != nil {
			return errors.Wrap(err, "unable to determine host IP address")
		}

		service = apiv1.Service{
			ObjectMeta: metav1.ObjectMeta{
				Name: "registry",
			},
			Spec: apiv1.ServiceSpec{
				Type:         apiv1.ServiceTypeExternalName,
				ExternalName: ipAddr,
				Selector: map[string]string{
					"app": "registry",
				},
			},
		}
	}

	servicesClient := k8sclient.CoreV1().Services("default")

	servicesClient.Delete(context.TODO(), "registry", *metav1.NewDeleteOptions(0))

	_, err = servicesClient.Create(context.TODO(), &service, metav1.CreateOptions{})

	if err != nil {
		return errors.Wrap(err, "unable to create ingress TLS secret")
	}

	return nil
}
