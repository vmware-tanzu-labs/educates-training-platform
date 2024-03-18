package diagnostics

import (
	"archive/tar"
	"compress/gzip"
	"context"
	"fmt"
	"io"
	"os"
	"path/filepath"

	"github.com/pkg/errors"
	"github.com/vmware-tanzu-labs/educates-training-platform/client-programs/pkg/cluster"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/runtime/schema"
	"k8s.io/cli-runtime/pkg/printers"
)

var workshopResource = schema.GroupVersionResource{Group: "training.educates.dev", Version: "v1beta1", Resource: "workshops"}

type ClusterDiagnostics struct {
	ClusterConfig *cluster.ClusterConfig
	Dir           string
	File          string
	tempDir       string
}

func NewClusterDiagnostics(clusterConfig *cluster.ClusterConfig, dir string, file string) *ClusterDiagnostics {
	return &ClusterDiagnostics{clusterConfig, dir, file, ""}
}

func (c *ClusterDiagnostics) Run() error {

	// Check if the cluster is available
	if !cluster.IsClusterAvailable(c.ClusterConfig) {
		return errors.New("cluster is not available")
	}

	// If directory is provided, check that it exists otherwise create it
	err := c.checkDirOrCreateTemp()
	if err != nil {
		return err
	}
	// TODO: Remove when working
	// if c.tempDir != "" {
	// 	defer os.RemoveAll(c.tempDir)
	// }

	// We save all the files in local Dir

	// getWorkshopDetailedList
	err = c.getWorkshopDetailedList()
	if err != nil {
		return err
	}
	// getEducatesNamespaces
	// getEducatesTrainingPortals
	// getEducatesWorkshops
	// fetch aggregrate educates resources, including training portal, workshop, and related resources
	// fetch EducatesSecrets

	// dump logs for all training-portal deployments, along with the list of workshops

	// fetch logs for the manager deploymentments

	// fetch events

	// if file is provided, compress the directory and save it to the file
	if c.File != "" {
		err = c.compressDir()
		if err != nil {
			return err
		}
		fmt.Println("Diagnostics files saved to file: ", c.File)
	} else {
		fmt.Println("Diagnostics files saved to dir: ", c.Dir)
	}

	fmt.Println("Diagnostics completed successfully")
	return nil
}

func (c *ClusterDiagnostics) checkDirOrCreateTemp() error {
	if c.Dir == "" {
		// Create a temporary directory
		tempDir, err := os.MkdirTemp("", "educates-diagnostics")
		if err != nil {
			return err
		}
		fmt.Println("Created temp dir: ", tempDir)
		c.Dir = tempDir
		c.tempDir = tempDir
	} else {
		// Check if the directory exists
		_, err := os.Stat(c.Dir)
		if os.IsNotExist(err) {
			// Create the directory
			err := os.MkdirAll(c.Dir, 0755)
			if err != nil {
				return err
			}
		}
	}

	return nil
}

func (c *ClusterDiagnostics) getWorkshopDetailedList() error {
	dynamicClient, err := c.ClusterConfig.GetDynamicClient()
	if err != nil {
		return err
	}
	workshopsClient := dynamicClient.Resource(workshopResource)

	workshops, err := workshopsClient.List(context.TODO(), metav1.ListOptions{})
	if err != nil {
		return err
	}

	newFile, err := os.Create(filepath.Join(c.Dir, "workshops.yaml"))
	if err != nil {
		return err
	}
	defer newFile.Close()

	y := printers.YAMLPrinter{}
	for _, workshop := range workshops.Items {
		workshop.SetManagedFields(nil) // Remove managedFields from the object
		if err := y.PrintObj(&workshop, newFile); err != nil {
			return err
		}
	}

	return nil
}

func (c *ClusterDiagnostics) compressDir() error {
	// We set the file name to the default if it is not provided
	if c.File == "" {
		c.File = "educates-diagnostics.tar.gz"
	}
	// Compress the directory into the file provided

	out, err := os.Create(c.File)
	if err != nil {
		errors.Errorf("Error writing archive:", err)
	}
	defer out.Close()

	files, err := filepath.Glob(filepath.Join(c.Dir, "*"))
	if err != nil {
		return err
	}

	gw := gzip.NewWriter(out)
	defer gw.Close()
	tw := tar.NewWriter(gw)
	defer tw.Close()

	// Iterate over files and add them to the tar archive
	for _, file := range files {
		err := c.addToArchive(tw, filepath.Join(c.Dir, file))
		if err != nil {
			return err
		}
	}

	return nil
}

func (c *ClusterDiagnostics) addToArchive(tw *tar.Writer, filename string) error {
	// Open the file which will be written into the archive
	file, err := os.Open(filename)
	if err != nil {
		return err
	}
	defer file.Close()

	// Get FileInfo about our file providing file size, mode, etc.
	info, err := file.Stat()
	if err != nil {
		return err
	}

	// Create a tar Header from the FileInfo data
	header, err := tar.FileInfoHeader(info, info.Name())
	if err != nil {
		return err
	}

	// Use full path as name (FileInfoHeader only takes the basename)
	// If we don't do this the directory strucuture would
	// not be preserved
	// https://golang.org/src/archive/tar/common.go?#L626
	// remove from filename the c.Dir
	header.Name, err = filepath.Rel(c.Dir, filename)
	if err != nil {
		return err
	}

	// Write file header to the tar archive
	err = tw.WriteHeader(header)
	if err != nil {
		return err
	}

	// Copy file content to tar archive
	_, err = io.Copy(tw, file)
	if err != nil {
		return err
	}

	return nil
}
