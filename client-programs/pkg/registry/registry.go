package registry

import (
	"archive/tar"
	"bytes"
	"compress/gzip"
	"context"
	"fmt"
	"io"
	"net"
	"os"
	"path"
	"strings"

	"github.com/docker/docker/api/types/container"
	"github.com/docker/docker/api/types/filters"
	"github.com/docker/docker/api/types/image"
	"github.com/docker/docker/api/types/network"
	"github.com/docker/docker/client"
	"github.com/docker/go-connections/nat"
	"github.com/pkg/errors"
	yttyaml "gopkg.in/yaml.v2"
	apiv1 "k8s.io/api/core/v1"
	v1 "k8s.io/api/core/v1"
	discoveryv1 "k8s.io/api/discovery/v1"
	k8serrors "k8s.io/apimachinery/pkg/api/errors"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/util/intstr"
	"k8s.io/client-go/kubernetes"
)

func DeployRegistry(bindIP string) error {
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

	reader, err := cli.ImagePull(ctx, "docker.io/library/registry:2", image.PullOptions{})
	if err != nil {
		return errors.Wrap(err, "cannot pull registry image")
	}

	defer reader.Close()
	io.Copy(os.Stdout, reader)

	_, err = cli.NetworkInspect(ctx, "educates", network.InspectOptions{})

	if err != nil {
		_, err = cli.NetworkCreate(ctx, "educates", network.CreateOptions{})

		if err != nil {
			return errors.Wrap(err, "cannot create educates network")
		}
	}

	hostConfig := &container.HostConfig{
		PortBindings: nat.PortMap{
			"5000/tcp": []nat.PortBinding{
				{
					HostIP:   bindIP,
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

	if err := cli.ContainerStart(ctx, resp.ID, container.StartOptions{}); err != nil {
		return errors.Wrap(err, "unable to start registry")
	}

	cli.NetworkDisconnect(ctx, "educates", "educates-registry", false)

	err = cli.NetworkConnect(ctx, "educates", "educates-registry", &network.EndpointSettings{})

	if err != nil {
		return errors.Wrap(err, "unable to connect registry to educates network")
	}

	return nil
}

func AddRegistryConfigToKindNodes(repositoryName string) error {
	ctx := context.Background()

	fmt.Printf("Adding local image registry config (%s) to Kind nodes\n", repositoryName)

	cli, err := client.NewClientWithOpts(client.FromEnv)

	if err != nil {
		return errors.Wrap(err, "unable to create docker client")
	}

	containerID, _ := getContainerInfo("educates-control-plane")

	registryDir := "/etc/containerd/certs.d/" + repositoryName

	cmdStatement := []string{"mkdir", "-p", registryDir}

	optionsCreateExecuteScript := container.ExecOptions{
		AttachStdout: true,
		AttachStderr: true,
		Cmd:          cmdStatement,
	}

	response, err := cli.ContainerExecCreate(ctx, containerID, optionsCreateExecuteScript)
	if err != nil {
		return errors.Wrap(err, "unable to create exec command")
	}
	hijackedResponse, err := cli.ContainerExecAttach(ctx, response.ID, container.ExecAttachOptions{})
	if err != nil {
		return errors.Wrap(err, "unable to attach exec command")
	}

	hijackedResponse.Close()

	content := `[host."http://educates-registry:5000"]`
	buffer, err := tarFile([]byte(content), path.Join("/etc/containerd/certs.d/"+repositoryName, "hosts.toml"), 0x644)
	if err != nil {
		return err
	}
	err = cli.CopyToContainer(context.Background(),
		containerID, "/",
		buffer,
		container.CopyToContainerOptions{
			AllowOverwriteDirWithFile: true,
		})
	if err != nil {
		return errors.Wrap(err, "unable to copy file to container")
	}

	return nil
}

func DocumentLocalRegistry(client *kubernetes.Clientset) error {
	yamlBytes, err := yttyaml.Marshal(`host: "localhost:5001"`)
	if err != nil {
		return err
	}

	configMap := &apiv1.ConfigMap{
		ObjectMeta: metav1.ObjectMeta{
			Name:      "local-registry-hosting",
			Namespace: "kube-public",
		},
		Data: map[string]string{
			"localRegistryHosting.v1": string(yamlBytes),
		},
	}

	if _, err := client.CoreV1().ConfigMaps("kube-public").Get(context.TODO(), "local-registry-hosting", metav1.GetOptions{}); k8serrors.IsNotFound(err) {
		_, err = client.CoreV1().ConfigMaps("kube-public").Create(context.TODO(), configMap, metav1.CreateOptions{})
		if err != nil {
			return errors.Wrap(err, "unable to create local registry hosting config map")
		}
	} else {
		_, err = client.CoreV1().ConfigMaps("kube-public").Update(context.TODO(), configMap, metav1.UpdateOptions{})
		if err != nil {
			return errors.Wrap(err, "unable to update local registry hosting config map")
		}
	}

	return nil
}

func LinkRegistryToCluster() error {
	ctx := context.Background()

	fmt.Println("Linking local image registry to cluster")

	cli, err := client.NewClientWithOpts(client.FromEnv)

	if err != nil {
		return errors.Wrap(err, "unable to create docker client")
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

	timeout := 30

	err = cli.ContainerStop(ctx, "educates-registry", container.StopOptions{Timeout: &timeout})

	// timeout := time.Duration(30) * time.Second

	// err = cli.ContainerStop(ctx, "educates-registry", &timeout)

	if err != nil {
		return errors.Wrap(err, "unable to stop registry container")
	}

	err = cli.ContainerRemove(ctx, "educates-registry", container.RemoveOptions{})

	if err != nil {
		return errors.Wrap(err, "unable to delete registry container")
	}

	return nil
}

func UpdateRegistryService(k8sclient *kubernetes.Clientset) error {
	ctx := context.Background()

	cli, err := client.NewClientWithOpts(client.FromEnv)

	if err != nil {
		return errors.Wrap(err, "unable to create docker client")
	}

	service := apiv1.Service{
		ObjectMeta: metav1.ObjectMeta{
			Name: "registry",
		},
		Spec: apiv1.ServiceSpec{
			Type: apiv1.ServiceTypeClusterIP,
			Ports: []apiv1.ServicePort{
				{
					Port:       80,
					TargetPort: intstr.FromInt(5001),
				},
			},
		},
	}

	endpointPort := int32(5000)
	endpointPortName := ""
	endpointAppProtocol := "http"
	endpointProtocol := v1.ProtocolTCP

	registryInfo, err := cli.ContainerInspect(ctx, "educates-registry")

	if err != nil {
		return errors.Wrapf(err, "unable to inspect container for registry")
	}

	kindNetwork, exists := registryInfo.NetworkSettings.Networks["kind"]

	if !exists {
		return errors.New("registry is not attached to kind network")
	}

	endpointAddresses := []string{kindNetwork.IPAddress}

	endpointSlice := discoveryv1.EndpointSlice{
		ObjectMeta: metav1.ObjectMeta{
			Name: "registry-1",
			Labels: map[string]string{
				"kubernetes.io/service-name": "registry",
			},
		},
		AddressType: "IPv4",
		Ports: []discoveryv1.EndpointPort{
			{
				Name:        &endpointPortName,
				AppProtocol: &endpointAppProtocol,
				Protocol:    &endpointProtocol,
				Port:        &endpointPort,
			},
		},
		Endpoints: []discoveryv1.Endpoint{
			{
				Addresses: endpointAddresses,
			},
		},
	}

	endpointSliceClient := k8sclient.DiscoveryV1().EndpointSlices("default")

	endpointSliceClient.Delete(context.TODO(), "registry-1", *metav1.NewDeleteOptions(0))

	servicesClient := k8sclient.CoreV1().Services("default")

	servicesClient.Delete(context.TODO(), "registry", *metav1.NewDeleteOptions(0))

	_, err = endpointSliceClient.Create(context.TODO(), &endpointSlice, metav1.CreateOptions{})

	if err != nil {
		return errors.Wrap(err, "unable to create registry headless service endpoint")
	}

	_, err = servicesClient.Create(context.TODO(), &service, metav1.CreateOptions{})

	if err != nil {
		return errors.Wrap(err, "unable to create registry headless service")
	}

	return nil
}

func PruneRegistry() error {
	ctx := context.Background()

	fmt.Println("Pruning local image registry")

	cli, err := client.NewClientWithOpts(client.FromEnv)

	if err != nil {
		return errors.Wrap(err, "unable to create docker client")
	}

	containerID, _ := getContainerInfo("educates-registry")

	cmdStatement := []string{"registry", "garbage-collect", "/etc/docker/registry/config.yml", "--delete-untagged=true"}

	optionsCreateExecuteScript := container.ExecOptions{
		AttachStdout: false,
		AttachStderr: false,
		Cmd:          cmdStatement,
	}

	response, err := cli.ContainerExecCreate(ctx, containerID, optionsCreateExecuteScript)
	if err != nil {
		return errors.Wrap(err, "unable to create exec command")
	}
	err = cli.ContainerExecStart(ctx, response.ID, container.ExecStartOptions{})
	if err != nil {
		return errors.Wrap(err, "unable to exec command")
	}

	fmt.Println("Registry pruned succesfully")

	return nil
}

func getContainerInfo(containerName string) (containerID string, status string) {
	ctx := context.Background()

	cli, err := client.NewClientWithOpts(client.FromEnv)
	if err != nil {
		panic(err)
	}

	filters := filters.NewArgs()
	filters.Add(
		"name", containerName,
	)

	resp, err := cli.ContainerList(ctx, container.ListOptions{Filters: filters})
	if err != nil {
		panic(err)
	}

	if len(resp) > 0 {
		containerID = resp[0].ID
		containerStatus := strings.Split(resp[0].Status, " ")
		status = containerStatus[0] //fmt.Println(status[0])
	} else {
		fmt.Printf("container '%s' does not exists\n", containerName)
	}

	return
}

func tarFile(fileContent []byte, basePath string, fileMode int64) (*bytes.Buffer, error) {
	buffer := &bytes.Buffer{}

	zr := gzip.NewWriter(buffer)
	tw := tar.NewWriter(zr)

	hdr := &tar.Header{
		Name: basePath,
		Mode: fileMode,
		Size: int64(len(fileContent)),
	}
	if err := tw.WriteHeader(hdr); err != nil {
		return buffer, err
	}
	if _, err := tw.Write(fileContent); err != nil {
		return buffer, err
	}

	// produce tar
	if err := tw.Close(); err != nil {
		return buffer, fmt.Errorf("error closing tar file: %w", err)
	}
	// produce gzip
	if err := zr.Close(); err != nil {
		return buffer, fmt.Errorf("error closing gzip file: %w", err)
	}

	return buffer, nil
}

func ValidateAndResolveIP(bindIP string) (string, error) {
	if bindIP == "" {
		return "", errors.New("bind ip cannot be empty")
	}

	ip := net.ParseIP(bindIP)
	if ip == nil {
		// Check if bindIP is a valid domain name
		ip, err := net.LookupHost(bindIP)
		if err != nil {
			return "", errors.New("bind ip is not a valid IP address or a domain name that resolves to an IP address")
		}
		return ip[0], nil
	}

	return ip.String(), nil
}
