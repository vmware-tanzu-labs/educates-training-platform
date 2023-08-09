// Copyright 2022-2023 The Educates Authors.

package cmd

import (
	"os"
	"path/filepath"

	"github.com/pkg/errors"
	"github.com/spf13/cobra"
	yttcmd "github.com/vmware-tanzu/carvel-ytt/pkg/cmd/template"
	"k8s.io/apimachinery/pkg/apis/meta/v1/unstructured"

	"github.com/vmware-tanzu-labs/educates-training-platform/client-programs/pkg/renderer"
)

func calculateWorkshopRoot(path string) (string, error) {
	var err error

	// If path not provided assume the current working directory.

	if path == "" {
		path = "."
	}

	path = filepath.Clean(path)

	if path, err = filepath.Abs(path); err != nil {
		return "", errors.Wrap(err, "couldn't convert workshop directory to absolute path")
	}

	fileInfo, err := os.Stat(path)

	if err != nil || !fileInfo.IsDir() {
		return "", errors.New("workshop directory does not exist or path is not a directory")
	}

	return path, nil
}

func calculateWorkshopName(name string, path string, portal string, workshopFile string, workshopVersion string, dataValuesFlags yttcmd.DataValuesFlags) (string, error) {
	var err error

	if name == "" {
		var workshop *unstructured.Unstructured

		if workshop, err = loadWorkshopDefinition(name, path, portal, workshopFile, workshopVersion, dataValuesFlags); err != nil {
			return "", err
		}

		name = workshop.GetName()
	}

	return name, nil
}

type ClusterWorkshopServeOptions struct {
	Name            string
	Path            string
	Kubeconfig      string
	Portal          string
	ProxyPort       int
	HugoPort        int
	Token           string
	Files           bool
	WorkshopFile    string
	WorkshopVersion string
	DataValuesFlags yttcmd.DataValuesFlags
}

func (o *ClusterWorkshopServeOptions) Run() error {
	var err error

	var name = o.Name
	var path = o.Path
	var portal = o.Portal

	// Ensure have portal name.

	if portal == "" {
		portal = "educates-cli"
	}

	// Calculate workshop root and name.

	if path, err = calculateWorkshopRoot(path); err != nil {
		return err
	}

	if name, err = calculateWorkshopName(name, path, portal, o.WorkshopFile, o.WorkshopVersion, o.DataValuesFlags); err != nil {
		return err
	}

	// Run the proxy server and Hugo server.

	return renderer.RunHugoServer(path, o.Kubeconfig, name, portal, o.ProxyPort, o.HugoPort, o.Token, o.Files)
}

func (p *ProjectInfo) NewClusterWorkshopServeCmd() *cobra.Command {
	var o ClusterWorkshopServeOptions

	var c = &cobra.Command{
		Args:  cobra.NoArgs,
		Use:   "server",
		Short: "Serve workshop from local system",
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
	c.Flags().StringVarP(
		&o.Portal,
		"portal",
		"p",
		"educates-cli",
		"name of the training portal to lookup the workshop",
	)
	c.Flags().IntVar(
		&o.ProxyPort,
		"proxy-port",
		10081,
		"port on which the proxy service will listen",
	)
	c.Flags().IntVar(
		&o.HugoPort,
		"hugo-port",
		1313,
		"port on which the hugo server will listen",
	)
	c.Flags().StringVarP(
		&o.Token,
		"token",
		"",
		"",
		"access token for protecting access to server",
	)
	c.Flags().BoolVarP(
		&o.Files,
		"allow-files-download",
		"",
		false,
		"enable download of workshop files as tarball",
	)

	c.Flags().StringVar(
		&o.WorkshopFile,
		"workshop-file",
		"resources/workshop.yaml",
		"location of the workshop definition file",
	)

	c.Flags().StringVar(
		&o.WorkshopVersion,
		"workshop-version",
		"latest",
		"version of the workshop being published",
	)

	c.Flags().StringArrayVar(
		&o.DataValuesFlags.EnvFromStrings,
		"data-values-env",
		nil,
		"Extract data values (as strings) from prefixed env vars (format: PREFIX for PREFIX_all__key1=str) (can be specified multiple times)",
	)
	c.Flags().StringArrayVar(
		&o.DataValuesFlags.EnvFromYAML,
		"data-values-env-yaml",
		nil,
		"Extract data values (parsed as YAML) from prefixed env vars (format: PREFIX for PREFIX_all__key1=true) (can be specified multiple times)",
	)

	c.Flags().StringArrayVar(
		&o.DataValuesFlags.KVsFromStrings,
		"data-value",
		nil,
		"Set specific data value to given value, as string (format: all.key1.subkey=123) (can be specified multiple times)",
	)
	c.Flags().StringArrayVar(
		&o.DataValuesFlags.KVsFromYAML,
		"data-value-yaml",
		nil,
		"Set specific data value to given value, parsed as YAML (format: all.key1.subkey=true) (can be specified multiple times)",
	)
	c.Flags().StringArrayVar(
		&o.DataValuesFlags.KVsFromFiles,
		"data-value-file",
		nil,
		"Set specific data value to contents of a file (format: [@lib1:]all.key1.subkey={file path, HTTP URL, or '-' (i.e. stdin)}) (can be specified multiple times)",
	)
	c.Flags().StringArrayVar(
		&o.DataValuesFlags.FromFiles,
		"data-values-file",
		nil,
		"Set multiple data values via plain YAML files (format: [@lib1:]{file path, HTTP URL, or '-' (i.e. stdin)}) (can be specified multiple times)",
	)

	return c
}
