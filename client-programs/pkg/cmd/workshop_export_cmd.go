// Copyright 2022-2023 The Educates Authors.

package cmd

import (
	"fmt"
	"os"
	"path/filepath"
	"strings"

	"github.com/pkg/errors"
	"github.com/spf13/cobra"
	yttcmd "github.com/vmware-tanzu/carvel-ytt/pkg/cmd/template"
	"gopkg.in/yaml.v2"
	"k8s.io/apimachinery/pkg/apis/meta/v1/unstructured"
	"k8s.io/apimachinery/pkg/runtime"
	"k8s.io/apimachinery/pkg/runtime/serializer"
	"k8s.io/kubectl/pkg/scheme"
)

type FilesExportOptions struct {
	Repository      string
	WorkshopFile    string
	WorkshopVersion string
	DataValuesFlags yttcmd.DataValuesFlags
}

func (o *FilesExportOptions) Run(args []string) error {
	var err error

	var directory string

	if len(args) != 0 {
		directory = filepath.Clean(args[0])
	} else {
		directory = "."
	}

	if directory, err = filepath.Abs(directory); err != nil {
		return errors.Wrap(err, "couldn't convert workshop directory to absolute path")
	}

	fileInfo, err := os.Stat(directory)

	if err != nil || !fileInfo.IsDir() {
		return errors.New("workshop directory does not exist or path is not a directory")
	}

	return o.Export(directory)
}

func (o *FilesExportOptions) Export(directory string) error {
	// If image name hasn't been supplied read workshop definition file and
	// try to work out image name to Export workshop as.

	rootDirectory := directory
	workshopFilePath := o.WorkshopFile

	if !filepath.IsAbs(workshopFilePath) {
		workshopFilePath = filepath.Join(rootDirectory, workshopFilePath)
	}

	workshopFileData, err := os.ReadFile(workshopFilePath)

	if err != nil {
		return errors.Wrapf(err, "cannot open workshop definition %q", workshopFilePath)
	}

	// Process the workshop YAML data for ytt templating and data variables.

	if workshopFileData, err = processWorkshopDefinition(workshopFileData, o.DataValuesFlags); err != nil {
		return errors.Wrap(err, "unable to process workshop definition as template")
	}

	workshopFileData = []byte(strings.ReplaceAll(string(workshopFileData), "$(image_repository)", o.Repository))
	workshopFileData = []byte(strings.ReplaceAll(string(workshopFileData), "$(workshop_version)", o.WorkshopVersion))

	decoder := serializer.NewCodecFactory(scheme.Scheme).UniversalDecoder()

	workshop := &unstructured.Unstructured{}

	err = runtime.DecodeInto(decoder, workshopFileData, workshop)

	if err != nil {
		return errors.Wrap(err, "couldn't parse workshop definition")
	}

	if workshop.GetAPIVersion() != "training.educates.dev/v1beta1" || workshop.GetKind() != "Workshop" {
		return errors.New("invalid type for workshop definition")
	}

	// Insert workshop version property if not specified.

	_, found, _ := unstructured.NestedString(workshop.Object, "spec", "version")

	if !found {
		unstructured.SetNestedField(workshop.Object, o.WorkshopVersion, "spec", "version")
	}

	// Export modified workshop definition file.

	workshopFileData, err = yaml.Marshal(&workshop.Object)

	if err != nil {
		return errors.Wrap(err, "couldn't convert workshop definition back to YAML")
	}

	fmt.Print(string(workshopFileData))

	return nil
}

func (p *ProjectInfo) NewWorkshopExportCmd() *cobra.Command {
	var o FilesExportOptions

	var c = &cobra.Command{
		Args:  cobra.MaximumNArgs(1),
		Use:   "export [PATH]",
		Short: "Export workshop resource definition",
		RunE:  func(cmd *cobra.Command, args []string) error { return o.Run(args) },
	}

	c.Flags().StringVar(
		&o.Repository,
		"repository",
		"localhost:5001",
		"the address of the image repository",
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
