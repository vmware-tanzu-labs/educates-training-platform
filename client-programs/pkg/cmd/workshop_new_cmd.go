// Copyright 2022 The Educates Authors.

package cmd

import (
	"bytes"
	"embed"
	"html/template"
	"os"
	"path"
	"path/filepath"

	"github.com/pkg/errors"
	"github.com/spf13/cobra"
)

//go:embed templates/*
var workshopTemplates embed.FS

type WorkshopNewOptions struct {
	Template    string
	Directory   string
	Title       string
	Description string
	Image       string
}

func (o *WorkshopNewOptions) Run() error {
	var err error

	directory := filepath.Clean(o.Directory)

	if directory, err = filepath.Abs(directory); err != nil {
		return errors.Wrap(err, "couldn't convert workshop directory to absolute path")
	}

	fileInfo, err := os.Stat(directory)

	if err != nil || !fileInfo.IsDir() {
		return errors.New("output directory does not exist or path is not a directory")
	}

	parameters := map[string]string{
		"WorkshopName":        filepath.Base(directory),
		"WorkshopTitle":       o.Title,
		"WorkshopDescription": o.Description,
		"WorkshopImage":       o.Image,
	}

	return applyTemplate(o.Template, directory, parameters)
}

func (p *ProjectInfo) NewWorkshopNewCmd() *cobra.Command {
	var o WorkshopNewOptions

	var c = &cobra.Command{
		Args:  cobra.NoArgs,
		Use:   "new-workshop",
		Short: "Create workshop from template",
		RunE:  func(_ *cobra.Command, _ []string) error { return o.Run() },
	}

	c.Flags().StringVarP(
		&o.Template,
		"template",
		"t",
		"default",
		"name of the workshop template to use",
	)
	c.Flags().StringVarP(
		&o.Directory,
		"file",
		"f",
		".",
		"path to the directory to add workshop to",
	)
	c.Flags().StringVar(
		&o.Title,
		"title",
		"",
		"short title describing the workshop",
	)
	c.Flags().StringVar(
		&o.Description,
		"description",
		"",
		"longer summary describing the workshop",
	)
	c.Flags().StringVar(
		&o.Image,
		"image",
		"",
		"name of the workshop base image to use",
	)

	return c
}

func applyTemplate(template string, directory string, parameters map[string]string) error {
	return copyTemplateDir(workshopTemplates, path.Join("templates", template), directory, parameters)
}

func copyTemplateDir(fs embed.FS, src string, dst string, parameters map[string]string) error {
	files, err := fs.ReadDir(src)

	if err != nil {
		return errors.Wrapf(err, "unable to open template directory %q", src)
	}

	for _, file := range files {
		srcFile := path.Join(src, file.Name())
		dstFile := path.Join(dst, file.Name())

		if file.IsDir() {
			if err = os.MkdirAll(dstFile, 0775); err != nil {
				return errors.Wrapf(err, "unable to create workshop directory %q", dstFile)
			}

			if err = copyTemplateDir(fs, srcFile, dstFile, parameters); err != nil {
				return err
			}
		} else {
			fileData, err := fs.ReadFile(srcFile)

			if err != nil {
				return errors.Wrapf(err, "unable to read template file %q", srcFile)
			}

			fileTemplate, err := template.New("template-file").Parse(string(fileData))

			if err != nil {
				return errors.Wrapf(err, "failed to parse template file %q", srcFile)
			}

			var fileOutData bytes.Buffer

			err = fileTemplate.Execute(&fileOutData, parameters)

			if err != nil {
				return errors.Wrapf(err, "failed to generate template file %q", srcFile)
			}

			newFile, err := os.Create(dstFile)

			if err != nil {
				return errors.Wrapf(err, "failed to create destination file %q", dstFile)
			}

			_, err = newFile.Write(fileOutData.Bytes())

			if err != nil {
				return errors.Wrapf(err, "unable to write destination file %q", dstFile)
			}

			// TODO Change permissions on files based on extension.
		}
	}

	return nil
}
