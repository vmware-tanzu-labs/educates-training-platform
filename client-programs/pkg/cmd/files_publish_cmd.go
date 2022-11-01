// Copyright 2022 The Educates Authors.

package cmd

import (
	"os"
	"path/filepath"
	"strings"

	"github.com/cppforlife/go-cli-ui/ui"
	"github.com/k14s/kapp/pkg/kapp/cmd"
	"github.com/pkg/errors"
	"github.com/spf13/cobra"
	imgpkgcmd "github.com/vmware-tanzu/carvel-imgpkg/pkg/imgpkg/cmd"
	"k8s.io/apimachinery/pkg/apis/meta/v1/unstructured"
	"k8s.io/apimachinery/pkg/runtime"
	"k8s.io/apimachinery/pkg/runtime/serializer"
	"k8s.io/kubectl/pkg/scheme"
)

type FilesPublishOptions struct {
	Directory  string
	Image      string
	Repository string
}

func (o *FilesPublishOptions) Run() error {
	var err error

	directory := filepath.Clean(o.Directory)

	if directory, err = filepath.Abs(directory); err != nil {
		return errors.Wrap(err, "couldn't convert workshop directory to absolute path")
	}

	fileInfo, err := os.Stat(directory)

	if err != nil || !fileInfo.IsDir() {
		return errors.New("workshop directory does not exist or path is not a directory")
	}

	return publishWorkshopDirectory(directory, o.Image, o.Repository)
}

func (p *ProjectInfo) NewFilesPublishCmd() *cobra.Command {
	var o FilesPublishOptions

	var c = &cobra.Command{
		Args:  cobra.NoArgs,
		Use:   "publish-files",
		Short: "Publish workshop files to repository",
		RunE:  func(_ *cobra.Command, _ []string) error { return o.Run() },
	}

	c.Flags().StringVarP(
		&o.Directory,
		"file",
		"f",
		".",
		"path to local workshop directory",
	)
	c.Flags().StringVar(
		&o.Image,
		"image",
		"",
		"name of the workshop files image artifact",
	)
	c.Flags().StringVar(
		&o.Repository,
		"repository",
		"localhost:5001",
		"the address of the image repository",
	)

	return c
}

func publishWorkshopDirectory(directory string, image string, repository string) error {
	// If image name hasn't been supplied read workshop definition file and
	// try to work out image name to publish workshop as.

	if image == "" {
		workshopFilePath := filepath.Join(directory, "resources", "workshop.yaml")

		workshopFileData, err := os.ReadFile(workshopFilePath)

		if err != nil {
			return errors.Wrapf(err, "cannot open workshop definition %q", workshopFilePath)
		}

		decoder := serializer.NewCodecFactory(scheme.Scheme).UniversalDecoder()

		workshop := &unstructured.Unstructured{}

		err = runtime.DecodeInto(decoder, workshopFileData, workshop)

		if err != nil {
			return errors.Wrap(err, "couldn't parse workshop definition")
		}

		fileArtifacts, found, err := unstructured.NestedSlice(workshop.Object, "spec", "workshop", "files")

		if err != nil || !found {
			return errors.Errorf("cannot find image specification in %q", workshopFilePath)
		}

		for _, artifactEntry := range fileArtifacts {
			if imageDetails, ok := artifactEntry.(map[string]interface{})["image"]; ok {
				if unpackPath, ok := artifactEntry.(map[string]interface{})["path"]; !ok || (ok && (unpackPath == nil || unpackPath.(string) == "" || unpackPath.(string) == ".")) {
					if imageUrl, ok := imageDetails.(map[string]interface{})["url"]; ok {
						image = strings.ReplaceAll(imageUrl.(string), "$(image_repository)", repository)
					}
				}
			}
		}
	}

	if image == "" {
		return errors.New("cannot determine name of image to publish as")
	}

	// Now publish workshop directory contents as OCI image artifact.

	confUI := ui.NewConfUI(ui.NewNoopLogger())

	uiFlags := cmd.UIFlags{
		Color:          true,
		JSON:           false,
		NonInteractive: true,
	}

	uiFlags.ConfigureUI(confUI)

	defer confUI.Flush()

	var pushOptions = imgpkgcmd.NewPushOptions(confUI)

	pushOptions.ImageFlags.Image = image
	pushOptions.FileFlags.Files = append(pushOptions.FileFlags.Files, directory)
	pushOptions.FileFlags.ExcludedFilePaths = append(pushOptions.FileFlags.ExcludedFilePaths, ".git")

	err := pushOptions.Run()

	if err != nil {
		return errors.Wrap(err, "unable to push image artifact for workshop")
	}

	return nil
}
