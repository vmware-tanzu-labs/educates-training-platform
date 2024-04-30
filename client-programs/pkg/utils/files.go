package utils

import (
	"fmt"
	"os"
	"path"
	"path/filepath"
	"slices"
	"strings"

	"carvel.dev/ytt/pkg/yamlmeta"
	"github.com/pkg/errors"
)

func PrintYamlFilesInDir(dir string, args []string) error {
	files, err := os.ReadDir(dir)

	if err != nil {
		return errors.Wrapf(err, "unable to read directory")
	}

	count := 0

	for _, f := range files {
		if strings.HasSuffix(f.Name(), ".yaml") {
			name := strings.TrimSuffix(f.Name(), ".yaml")
			fullPath := path.Join(dir, f.Name())

			if len(args) == 0 || slices.Contains(args, name) {
				yamlData, err := os.ReadFile(fullPath)

				if err != nil {
					continue
				}

				if len(yamlData) == 0 || string(yamlData) == "\n" {
					continue
				}

				if count != 0 {
					fmt.Println("---")
				}

				fmt.Print(string(yamlData))

				count = count + 1
			}
		}
	}
	return nil
}

func WriteYamlByteArrayItemsToDir(files [][]byte, dir string) error {
	for i, doc := range files {
		file, err := os.Create(filepath.Join(dir, fmt.Sprintf("install_%.3d.yaml", i)))
		if err != nil {
			fmt.Printf("Failed to create file: %v\n", err)
			return err
		}
		defer file.Close()

		_, err = file.Write(doc)
		if err != nil {
			fmt.Printf("Failed to write to file: %v\n", err)
			return err
		}
	}
	return nil
}

func WriteYamlDocSetItemsToDir(fileSet *yamlmeta.DocumentSet, dir string) error {
	for i, doc := range fileSet.Items {
		file, err := os.Create(filepath.Join(dir, fmt.Sprintf("install_%.3d.yaml", i)))
		if err != nil {
			fmt.Printf("Failed to create file: %v\n", err)
			return err
		}
		defer file.Close()

		// Write the doc to the file
		bytes, _ := doc.AsYAMLBytes()
		_, err = file.WriteString(string(bytes))
		if err != nil {
			fmt.Printf("Failed to write to file: %v\n", err)
			return err
		}
	}
	return nil
}
