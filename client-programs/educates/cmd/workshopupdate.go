/*
Copyright © 2022 The Educates Authors.
*/
package cmd

import (
	"context"
	"crypto/sha1"
	"fmt"
	"io"
	"net/http"
	"net/url"
	"os"
	"path/filepath"

	"github.com/pkg/errors"
	"github.com/spf13/cobra"
	"github.com/vmware-tanzu-labs/educates-training-platform/client-programs/educates/pkg/cluster"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/apis/meta/v1/unstructured"
	"k8s.io/apimachinery/pkg/runtime"
	"k8s.io/apimachinery/pkg/runtime/schema"
	"k8s.io/apimachinery/pkg/runtime/serializer"
	"k8s.io/client-go/dynamic"
	"k8s.io/kubectl/pkg/scheme"
)

type WorkshopUpdateOptions struct {
	Name       string
	Path       string
	Kubeconfig string
}

func (o *WorkshopUpdateOptions) Run() error {
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

	if workshop, err = loadWorkshopDefinition(o.Name, path); err != nil {
		return err
	}

	clusterConfig := cluster.NewClusterConfig(o.Kubeconfig)

	dynamicClient, err := clusterConfig.GetDynamicClient()

	if err != nil {
		return errors.Wrapf(err, "unable to create Kubernetes client")
	}

	// Update the workshop definition in the Kubernetes cluster.

	err = updateWorkshopDefinition(dynamicClient, workshop)

	if err != nil {
		return err
	}

	return nil
}

func NewWorkshopUpdateCmd() *cobra.Command {
	var o WorkshopUpdateOptions

	var c = &cobra.Command{
		Args:  cobra.NoArgs,
		Use:   "update-workshop",
		Short: "Update the workshop definition",
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
	c.Flags().StringVar(
		&o.Kubeconfig,
		"kubeconfig",
		"",
		"kubeconfig file to use instead of $KUBECONFIG or $HOME/.kube/config",
	)

	return c
}

func loadWorkshopDefinition(name string, path string) (*unstructured.Unstructured, error) {
	// Parse the workshop location so we can determine if it is a local file
	// or accessible using a HTTP/HTTPS URL.

	var urlInfo *url.URL
	var err error

	if urlInfo, err = url.Parse(path); err != nil {
		return nil, errors.Wrap(err, "unable to parse workshop location")
	}

	// Check if file system path first (not HTTP/HTTPS) and if so normalize
	// the path. If it the path references a directory, then extend the path
	// so we look for the resources/workshop.yaml file within that directory.

	if urlInfo.Scheme != "http" && urlInfo.Scheme != "https" {
		path = filepath.Clean(path)

		if path, err = filepath.Abs(path); err != nil {
			return nil, errors.Wrap(err, "couldn't convert workshop location to absolute path")
		}

		fileInfo, err := os.Stat(path)

		if err != nil {
			return nil, errors.Wrap(err, "couldn't test if workshop location is a directory")
		}

		if fileInfo.IsDir() {
			path = filepath.Join(path, "resources", "workshop.yaml")
		}
	}

	// Read in the workshop definition as raw data ready for parsing.

	var workshopData []byte

	if urlInfo.Scheme != "http" && urlInfo.Scheme != "https" {
		if workshopData, err = os.ReadFile(path); err != nil {
			return nil, errors.Wrap(err, "couldn't read workshop definition data file")
		}
	} else {
		var client http.Client

		resp, err := client.Get(path)

		if err != nil {
			return nil, errors.Wrap(err, "couldn't download workshop definition from host")
		}

		defer resp.Body.Close()

		if resp.StatusCode != http.StatusOK {
			return nil, errors.New("failed to download workshop definition from host")
		}

		workshopData, err = io.ReadAll(resp.Body)

		if err != nil {
			return nil, errors.Wrap(err, "failed to read workshop definition from host")
		}
	}

	// Parse the workshop definition.

	decoder := serializer.NewCodecFactory(scheme.Scheme).UniversalDecoder()

	workshop := &unstructured.Unstructured{}

	err = runtime.DecodeInto(decoder, workshopData, workshop)

	if err != nil {
		return nil, errors.Wrap(err, "couldn't parse workshop definition")
	}

	// Verify the type of resource definition.

	if workshop.GetAPIVersion() != "training.educates.dev/v1beta1" || workshop.GetKind() != "Workshop" {
		return nil, errors.New("invalid type for workshop definition")
	}

	// Add annotations recording details about original workshop location.

	annotations := workshop.GetAnnotations()

	if annotations == nil {
		annotations = map[string]string{}
	}

	annotations["training.educates.dev/workshop"] = workshop.GetName()

	if urlInfo.Scheme != "http" && urlInfo.Scheme != "https" {
		annotations["training.educates.dev/location"] = fmt.Sprintf("file://%s", path)
	} else {
		annotations["training.educates.dev/location"] = path
	}

	workshop.SetAnnotations(annotations)

	// Update the name for the workshop such that it incorporates a hash of
	// the workshop location.

	if name == "" {
		name = generateWorkshopName(path, workshop)
	}

	workshop.SetName(name)

	return workshop, nil
}

func generateWorkshopName(path string, workshop *unstructured.Unstructured) string {
	name := workshop.GetName()

	h := sha1.New()

	io.WriteString(h, path)

	hv := fmt.Sprintf("%x", h.Sum(nil))

	name = fmt.Sprintf("educates--%s-%s", name, hv[len(hv)-7:])

	return name
}

var workshopResource = schema.GroupVersionResource{Group: "training.educates.dev", Version: "v1beta1", Resource: "workshops"}

func updateWorkshopDefinition(client dynamic.Interface, workshop *unstructured.Unstructured) error {
	workshopsClient := client.Resource(workshopResource)

	_, err := workshopsClient.Apply(context.TODO(), workshop.GetName(), workshop, metav1.ApplyOptions{FieldManager: "educates-cli", Force: true})

	if err != nil {
		return errors.Wrapf(err, "unable to update workshop definition in cluster %q", workshop.GetName())
	}

	return nil
}
