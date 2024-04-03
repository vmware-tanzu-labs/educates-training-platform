package diagnostics

import (
	"fmt"
	"io"
	"os"
	"path/filepath"

	"github.com/pkg/errors"
	"github.com/vmware-tanzu-labs/educates-training-platform/client-programs/pkg/cluster"
)

type ClusterDiagnostics struct {
	clusterConfig *cluster.ClusterConfig
	dest          string
}

func NewClusterDiagnostics(clusterConfig *cluster.ClusterConfig, dest string) *ClusterDiagnostics {
	return &ClusterDiagnostics{clusterConfig, dest}
}

func (c *ClusterDiagnostics) Run() error {
	// Check if the cluster is available
	if !cluster.IsClusterAvailable(c.clusterConfig) {
		return errors.New("cluster is not available")
	}

	tempDir, err := createTempDir()
	if err != nil {
		return err
	}
	fmt.Println("Created temp dir: ", tempDir)
	defer os.RemoveAll(tempDir)

	clusterDiagnosticsFetcher := &ClusterDiagnosticsFetcher{c.clusterConfig, tempDir}
	// getEducatesTrainingPortals
	err = clusterDiagnosticsFetcher.fetchDynamicallyResources(trainingportalResource, "training-portals.yaml")
	if err != nil {
		fmt.Println("Error fetching training portals: ", err)
	}
	// getEducatesWorkshops
	err = clusterDiagnosticsFetcher.fetchDynamicallyResources(workshopResource, "workshops.yaml")
	if err != nil {
		fmt.Println("Error fetching workshops: ", err)
	}
	err = clusterDiagnosticsFetcher.fetchDynamicallyResources(workshopsessionsResource, "educates-workshop-sessions.yaml")
	if err != nil {
		fmt.Println("Error fetching workshop sessions: ", err)
	}
	err = clusterDiagnosticsFetcher.fetchDynamicallyResources(workshoprequestsResource, "educates-workshop-requests.yaml")
	if err != nil {
		fmt.Println("Error fetching workshop requests: ", err)
	}
	err = clusterDiagnosticsFetcher.fetchDynamicallyResources(workshopenvironmentsResource, "educates-workshop-environments.yaml")
	if err != nil {
		fmt.Println("Error fetching workshop environments: ", err)
	}
	err = clusterDiagnosticsFetcher.fetchDynamicallyResources(workshopallocationsResource, "educates-workshop-allocations.yaml")
	if err != nil {
		fmt.Println("Error fetching workshop allocations: ", err)
	}

	//	getEducatesNamespaces
	err = clusterDiagnosticsFetcher.getEducatesNamespaces()
	if err != nil {
		fmt.Println("Error fetching educates namespaces: ", err)
	}

	// fetch EducatesSecrets
	err = clusterDiagnosticsFetcher.fetchDynamicallyResources(secretcopierResource, "educates-secret-copiers.yaml")
	if err != nil {
		fmt.Println("Error fetching secret copiers: ", err)
	}
	err = clusterDiagnosticsFetcher.fetchDynamicallyResources(secretinjectorsResource, "educates-secret-injectors.yaml")
	if err != nil {
		fmt.Println("Error fetching secret injectors: ", err)
	}
	err = clusterDiagnosticsFetcher.fetchDynamicallyResources(secretexportersResource, "educates-secret-exporters.yaml")
	if err != nil {
		fmt.Println("Error fetching secret injectors: ", err)
	}
	err = clusterDiagnosticsFetcher.fetchDynamicallyResources(secretimportersResource, "educates-secret-importers.yaml")
	if err != nil {
		fmt.Println("Error fetching secret injectors: ", err)
	}

	// fetch logs for the session-manager, secret-manager deploymentments
	err = clusterDiagnosticsFetcher.fetchLogsForDeployment("deployment=session-manager", "educates", "session-manager.log")
	if err != nil {
		fmt.Println("Error fetching logs for session-manager: ", err)
	}
	err = clusterDiagnosticsFetcher.fetchLogsForDeployment("deployment=secrets-manager", "educates", "secrets-manager.log")
	if err != nil {
		fmt.Println("Error fetching logs for secrets-manager: ", err)
	}
	// dump logs for all training-portal deployments
	err = clusterDiagnosticsFetcher.fetchLogsForDeployment("deployment=training-portal", "training.educates.dev/component=portal", "training-portal-%v.log")
	if err != nil {
		fmt.Println("Error fetching logs for secrets-manager: ", err)
	}
	// TODO: fetch workshop_list from Rest API for each training-portal

	// fetch events
	err = clusterDiagnosticsFetcher.getEducatesNamespacesEvents()
	if err != nil {
		fmt.Println("Error fetching educates namespaces: ", err)
	}

	// If directory is provided, check that it exists otherwise create it
	dir, file, err := getDestDirAndFile(c.dest)
	if err != nil {
		return err
	}

	// if file is provided, compress the directory and save it to the file
	// else, copy all the files from the tempDir to the provided directory
	if file != "" {
		err = CompressDirToFile(tempDir, c.dest)
		if err != nil {
			return err
		}
		fmt.Println("Diagnostics files saved to file: ", c.dest)
	} else {
		copyAllFilesInDir(tempDir, dir)
		fmt.Println("Diagnostics files saved to dir: ", dir)
	}

	fmt.Println("Diagnostics completed successfully")
	return nil
}

// func (c *ClusterDiagnostics) checkDestination() error {
// 	if c.dir == "" {
// 		// Create a temporary directory
// 		tempDir, err := os.MkdirTemp("", "educates-diagnostics")
// 		if err != nil {
// 			return err
// 		}
// 		fmt.Println("Created temp dir: ", tempDir)
// 		c.dir = tempDir
// 	} else {
// 		// Check if the directory exists
// 		_, err := os.Stat(c.dir)
// 		if os.IsNotExist(err) {
// 			// Create the directory
// 			err := os.MkdirAll(c.dir, 0755)
// 			if err != nil {
// 				return err
// 			}
// 		}
// 	}

// 	return nil
// }

func createTempDir() (string, error) {
	tempDir, err := os.MkdirTemp("", "educates-diagnostics")
	if err != nil {
		return "", err
	}
	return tempDir, nil
}

func getDestDirAndFile(dest string) (string, string, error) {
	if dest == "" {
		return "", "", fmt.Errorf("dest is required")
	}
	if filepath.Ext(dest) == ".tar.gz" {
		return filepath.Dir(dest), filepath.Base(dest), nil
	} else if filepath.Ext(dest) == "" {
		return dest, "", nil
	} else {
		return "", "", fmt.Errorf("dest must be a directory or a .tar.gz file")
	}
}

func copyAllFilesInDir(src string, dest string) error {
	return filepath.Walk(src, func(path string, info os.FileInfo, err error) error {
		if err != nil {
			return err
		}
		// We only copy the files in the temp directory, if it's a dir, we skip it
		if info.IsDir() {
			return nil
		}
		// Get the relative path of the file
		relPath, err := filepath.Rel(src, path)
		if err != nil {
			return err
		}
		// Create the destination path
		destPath := filepath.Join(dest, relPath)

		// Create the directory if it doesn't exist
		if err := os.MkdirAll(filepath.Dir(destPath), 0755); err != nil {
			return err
		}

		// Copy the file
		srcFile, err := os.Open(path)
		if err != nil {
			return err
		}
		defer srcFile.Close()
		destFile, err := os.Create(destPath)
		if err != nil {
			return err
		}
		defer destFile.Close()
		_, err = io.Copy(destFile, srcFile)
		return err
	})
}
