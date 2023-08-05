// Copyright 2022-2023 The Educates Authors.

package cmd

import (
	"fmt"
	"io/ioutil"
	"os"
	"path/filepath"
	"strings"

	"github.com/cppforlife/go-cli-ui/ui"
	"github.com/pkg/errors"
	"github.com/spf13/cobra"
	imgpkgcmd "github.com/vmware-tanzu/carvel-imgpkg/pkg/imgpkg/cmd"
	"github.com/vmware-tanzu/carvel-kapp/pkg/kapp/cmd"
	vendirsync "github.com/vmware-tanzu/carvel-vendir/pkg/vendir/cmd"
	"gopkg.in/yaml.v2"
	"k8s.io/apimachinery/pkg/apis/meta/v1/unstructured"
	"k8s.io/apimachinery/pkg/runtime"
	"k8s.io/apimachinery/pkg/runtime/serializer"
	"k8s.io/kubectl/pkg/scheme"

	"github.com/vmware-tanzu-labs/educates-training-platform/client-programs/pkg/registry"
)

type FilesPublishOptions struct {
	Image          string
	Repository     string
	WorkshopFile   string
	ExportWorkshop string
}

func (p *ProjectInfo) NewWorkshopPublishCmd() *cobra.Command {
	var o FilesPublishOptions

	var c = &cobra.Command{
		Args:  cobra.MaximumNArgs(1),
		Use:   "publish [PATH]",
		Short: "Publish workshop files to repository",
		RunE: func(_ *cobra.Command, args []string) error {
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

			if o.Repository == "localhost:5001" {
				err = registry.DeployRegistry()

				if err != nil {
					return errors.Wrap(err, "failed to deploy registry")
				}
			}

			return publishWorkshopDirectory(directory, o.Image, o.Repository, o.WorkshopFile, o.ExportWorkshop)
		},
	}

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
	c.Flags().StringVar(
		&o.WorkshopFile,
		"workshop-file",
		"resources/workshop.yaml",
		"location of the workshop definition file",
	)
	c.Flags().StringVar(
		&o.ExportWorkshop,
		"export-workshop",
		"",
		"location to save modified workshop file",
	)

	return c
}

func publishWorkshopDirectory(directory string, image string, repository string, workshopFile string, exportWorkshop string) error {
	// If image name hasn't been supplied read workshop definition file and
	// try to work out image name to publish workshop as.

	rootDirectory := directory

	workingDirectory, err := os.Getwd()

	if err != nil {
		return errors.Wrap(err, "cannot determine current working directory")
	}

	includePaths := []string{directory}
	excludePaths := []string{".git"}

	workshopFilePath := filepath.Join(directory, workshopFile)

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

	if image == "" {
		image, _, _ = unstructured.NestedString(workshop.Object, "spec", "publish", "image")
		image = strings.ReplaceAll(image, "$(image_repository)", repository)
	}

	if image == "" {
		fileArtifacts, found, _ := unstructured.NestedSlice(workshop.Object, "spec", "workshop", "files")

		if found {
			for _, artifactEntry := range fileArtifacts {
				if imageDetails, ok := artifactEntry.(map[string]interface{})["image"]; ok {
					if unpackPath, ok := artifactEntry.(map[string]interface{})["path"]; !ok || (ok && (unpackPath == nil || unpackPath.(string) == "" || unpackPath.(string) == ".")) {
						if imageUrl, ok := imageDetails.(map[string]interface{})["url"]; ok {
							image = strings.ReplaceAll(imageUrl.(string), "$(image_repository)", repository)

							if newRootPath, ok := artifactEntry.(map[string]interface{})["newRootPath"]; ok {
								suffix := "/" + newRootPath.(string)
								if strings.HasSuffix(directory, suffix) {
									rootDirectory = strings.TrimSuffix(directory, suffix)
									includePaths = []string{rootDirectory}
								}
							}
						}
					}
				}
			}
		}

		if image == "" {
			fileArtifacts, found, _ := unstructured.NestedSlice(workshop.Object, "spec", "environment", "assets", "files")

			if found {
				for _, artifactEntry := range fileArtifacts {
					if imageDetails, ok := artifactEntry.(map[string]interface{})["image"]; ok {
						if unpackPath, ok := artifactEntry.(map[string]interface{})["path"]; !ok || (ok && (unpackPath == nil || unpackPath.(string) == "" || unpackPath.(string) == ".")) {
							if imageUrl, ok := imageDetails.(map[string]interface{})["url"]; ok {
								image = strings.ReplaceAll(imageUrl.(string), "$(image_repository)", repository)

								if newRootPath, ok := artifactEntry.(map[string]interface{})["newRootPath"]; ok {
									suffix := "/" + newRootPath.(string)
									if strings.HasSuffix(directory, suffix) {
										rootDirectory = strings.TrimSuffix(directory, suffix)
										includePaths = []string{rootDirectory}
									}
								}
							}
						}
					}
				}
			}
		}
	}

	if image == "" {
		return errors.Errorf("cannot find image specification in %q", workshopFilePath)
	}

	// Extract vendir snippet describing subset of files to package up as the
	// workshop image.

	confUI := ui.NewConfUI(ui.NewNoopLogger())

	uiFlags := cmd.UIFlags{
		Color:          true,
		JSON:           false,
		NonInteractive: true,
	}

	uiFlags.ConfigureUI(confUI)

	defer confUI.Flush()

	if fileArtifacts, found, _ := unstructured.NestedSlice(workshop.Object, "spec", "publish", "files"); found && len(fileArtifacts) != 0 {
		tempDir, err := ioutil.TempDir("", "educates-imgpkg")

		if err != nil {
			return errors.Wrapf(err, "unable to create temporary working directory")
		}

		defer os.RemoveAll(tempDir)

		vendirConfig := map[string]interface{}{
			"apiVersion":  "vendir.k14s.io/v1alpha1",
			"kind":        "Config",
			"directories": []interface{}{},
		}

		for _, artifactEntry := range fileArtifacts {
			dir := filepath.Join(tempDir, "files")

			if filePath, found := artifactEntry.(map[string]interface{})["path"].(string); found {
				dir = filepath.Join(tempDir, "files", filepath.Clean(filePath))
			}

			if directoryConfig, found := artifactEntry.(map[string]interface{})["directory"]; found {
				if directoryPath, found := directoryConfig.(map[string]interface{})["path"].(string); found {
					if !filepath.IsAbs(directoryPath) {
						directoryConfig.(map[string]interface{})["path"] = filepath.Join(directory, directoryPath)
					}
				}
			}

			artifactEntry.(map[string]interface{})["path"] = "."

			directoryConfig := map[string]interface{}{
				"path":     dir,
				"contents": []interface{}{artifactEntry},
			}

			vendirConfig["directories"] = append(vendirConfig["directories"].([]interface{}), directoryConfig)
		}

		yamlData, err := yaml.Marshal(&vendirConfig)

		if err != nil {
			return errors.Wrap(err, "unable to generate vendir config")
		}

		vendirConfigFile, err := os.Create(filepath.Join(tempDir, "vendir.yml"))

		if err != nil {
			return errors.Wrap(err, "unable to create vendir config file")
		}

		defer vendirConfigFile.Close()

		_, err = vendirConfigFile.Write(yamlData)

		if err != nil {
			return errors.Wrap(err, "unable to write vendir config file")
		}

		syncOptions := vendirsync.NewSyncOptions(confUI)

		syncOptions.Directories = nil
		syncOptions.Files = []string{filepath.Join(tempDir, "vendir.yml")}

		// Note that Chdir here actually changes the process working directory.

		syncOptions.LockFile = "lock-file"
		syncOptions.Locked = false
		syncOptions.Chdir = tempDir
		syncOptions.AllowAllSymlinkDestinations = false

		if err = syncOptions.Run(); err != nil {
			fmt.Println(string(yamlData))

			return errors.Wrap(err, "failed to prepare image files for publishing")
		}

		// Restore working directory as was changed.

		os.Chdir((workingDirectory))

		rootDirectory = filepath.Join(tempDir, "files")
		includePaths = []string{rootDirectory}
	}

	// Now publish workshop directory contents as OCI image artifact.

	pushOptions := imgpkgcmd.NewPushOptions(confUI)

	pushOptions.ImageFlags.Image = image
	pushOptions.FileFlags.Files = append(pushOptions.FileFlags.Files, includePaths...)
	pushOptions.FileFlags.ExcludedFilePaths = append(pushOptions.FileFlags.ExcludedFilePaths, excludePaths...)

	err = pushOptions.Run()

	if err != nil {
		return errors.Wrap(err, "unable to push image artifact for workshop")
	}

	// Export modified workshop definition file.

	if exportWorkshop != "" {
		if !filepath.IsAbs(exportWorkshop) {
			exportWorkshop = filepath.Join(workingDirectory, exportWorkshop)
		}

		workshopFileData = []byte(strings.ReplaceAll(string(workshopFileData), "$(image_repository)", repository))

		exportWorkshopFile, err := os.Create(exportWorkshop)

		if err != nil {
			return errors.Wrap(err, "unable to create exported workshop definition file")
		}

		defer exportWorkshopFile.Close()

		_, err = exportWorkshopFile.Write(workshopFileData)

		if err != nil {
			return errors.Wrap(err, "unable to write exported workshop definition file")
		}
	}

	return nil
}
