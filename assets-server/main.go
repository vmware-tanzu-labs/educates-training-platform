/*
 * This is a Golang application that serves static files from a specified
 * directory and can also create and serve tar and zip archives of directories
 * from the same directory.
 *
 * The application uses the cobra package for command-line argument handling. It
 * allows the user to specify the directory path from which static files are
 * served, the port the server listens on, and the host interface the listener
 * socket is bound to.
 *
 * The server can handle the following types of requests:
 *   - Requests for regular static files (e.g., http://localhost:8080/file.txt)
 *   - Requests for tar archives of directories (e.g., http://localhost:8080/subdir/.tar)
 *   - Requests for tar.gz or .tgz archives of directories (e.g., http://localhost:8080/subdir/.tar.gz)
 *   - Requests for zip archives of directories (e.g., http://localhost:8080/subdir/.zip)
 */

package main

import (
	"archive/tar"
	"archive/zip"
	"compress/gzip"
	"fmt"
	"io"
	"log"
	"net/http"
	"os"
	"path/filepath"
	"strings"

	"github.com/spf13/cobra"
)

func createTarArchive(dirPath string, writer io.Writer, compress bool) error {
	var tarWriter *tar.Writer
	if compress {
		gzipWriter := gzip.NewWriter(writer)
		defer gzipWriter.Close()
		tarWriter = tar.NewWriter(gzipWriter)
	} else {
		tarWriter = tar.NewWriter(writer)
	}
	defer tarWriter.Close()

	return filepath.Walk(dirPath, func(path string, info os.FileInfo, err error) error {
		if err != nil {
			return err
		}

		relPath, err := filepath.Rel(dirPath, path)
		if err != nil {
			return err
		}

		// Create a new tar header
		header, err := tar.FileInfoHeader(info, "")
		if err != nil {
			return err
		}
		header.Name = filepath.ToSlash(relPath)

		// Write the header to the tar archive
		if err := tarWriter.WriteHeader(header); err != nil {
			return err
		}

		// If the file is not a directory, write its content to the tar archive
		if !info.IsDir() {
			file, err := os.Open(path)
			if err != nil {
				return err
			}
			defer file.Close()

			_, err = io.Copy(tarWriter, file)
			if err != nil {
				return err
			}
		}

		return nil
	})
}

func createZipArchive(dirPath string, writer io.Writer) error {
	zipWriter := zip.NewWriter(writer)
	defer zipWriter.Close()

	return filepath.Walk(dirPath, func(path string, info os.FileInfo, err error) error {
		if err != nil {
			return err
		}

		relPath, err := filepath.Rel(dirPath, path)
		if err != nil {
			return err
		}

		// Create a new zip header
		header, err := zip.FileInfoHeader(info)
		if err != nil {
			return err
		}
		header.Name = filepath.ToSlash(relPath)

		// Write the header to the zip archive
		writer, err := zipWriter.CreateHeader(header)
		if err != nil {
			return err
		}

		// If the file is not a directory, write its content to the zip archive
		if !info.IsDir() {
			file, err := os.Open(path)
			if err != nil {
				return err
			}
			defer file.Close()

			_, err = io.Copy(writer, file)
			if err != nil {
				return err
			}
		}

		return nil
	})
}

func main() {
	var rootCmd = &cobra.Command{
		Use:   "static-server",
		Short: "Serve static files from a directory",
		Run:   startServer,
	}

	var dataDir string
	var port string
	var host string

	rootCmd.Flags().StringVarP(&dataDir, "dir", "d", "data", "Directory path containing static files")
	rootCmd.Flags().StringVarP(&port, "port", "p", "8080", "Port number to listen on")
	rootCmd.Flags().StringVarP(&host, "host", "H", "localhost", "Host interface to bind the listener socket")

	if err := rootCmd.Execute(); err != nil {
		fmt.Println(err)
		os.Exit(1)
	}
}

func startServer(cmd *cobra.Command, args []string) {
	dataDir, _ := cmd.Flags().GetString("dir")
	port, _ := cmd.Flags().GetString("port")
	host, _ := cmd.Flags().GetString("host")

	// Check if the data directory exists
	_, err := os.Stat(dataDir)
	if err != nil {
		if os.IsNotExist(err) {
			fmt.Println("Directory", dataDir, "does not exist. Please create the directory and put your static files in it.")
			return
		}
		fmt.Println("Error:", err)
		return
	}

	// Middleware for logging HTTP requests
	loggingMiddleware := func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			log.Printf("Incoming request: %s %s", r.Method, r.URL.Path)
			next.ServeHTTP(w, r)
		})
	}

	// Create a file server handler to serve static files from the data directory
	fileServer := http.FileServer(http.Dir(dataDir))

	// Handle requests for tar, tar.gz, or zip archives of directories
	http.Handle("/", loggingMiddleware(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		requestedPath := r.URL.Path

		// Check if the requested path ends with ".tar", ".tar.gz" or ".tgz"
		if strings.HasSuffix(requestedPath, "/.tar") {
			// Remove the ".tar" suffix from the path
			requestedPath = strings.TrimSuffix(requestedPath, ".tar")

			// Check if the path maps to a directory
			fileInfo, err := os.Stat(filepath.Join(dataDir, requestedPath))
			if err != nil || !fileInfo.IsDir() {
				// Serve static files as the path does not map to a directory
				fileServer.ServeHTTP(w, r)
				return
			}

			// Serve the tar archive for the requested directory
			w.Header().Set("Content-Type", "application/x-tar")
			w.Header().Set("Content-Disposition", fmt.Sprintf("attachment; filename=\"%s.tar\"", requestedPath))

			err = createTarArchive(filepath.Join(dataDir, requestedPath), w, false)
			if err != nil {
				http.Error(w, "Error creating tar archive", http.StatusInternalServerError)
				return
			}
			return
		} else if strings.HasSuffix(requestedPath, "/.tar.gz") || strings.HasSuffix(requestedPath, "/.tgz") {
			// Remove the ".tar.gz" or ".tgz" suffix from the path
			requestedPath = strings.TrimSuffix(requestedPath, ".tar.gz")
			requestedPath = strings.TrimSuffix(requestedPath, ".tgz")

			// Check if the path maps to a directory
			fileInfo, err := os.Stat(filepath.Join(dataDir, requestedPath))
			if err != nil || !fileInfo.IsDir() {
				// Serve static files as the path does not map to a directory
				fileServer.ServeHTTP(w, r)
				return
			}

			// Serve the tar.gz archive for the requested directory
			w.Header().Set("Content-Type", "application/gzip")
			w.Header().Set("Content-Disposition", fmt.Sprintf("attachment; filename=\"%s.tar.gz\"", requestedPath))

			err = createTarArchive(filepath.Join(dataDir, requestedPath), w, true)
			if err != nil {
				http.Error(w, "Error creating tar.gz archive", http.StatusInternalServerError)
				return
			}
			return
		} else if strings.HasSuffix(requestedPath, "/.zip") {
			// Remove the ".zip" suffix from the path
			requestedPath = strings.TrimSuffix(requestedPath, ".zip")

			// Check if the path maps to a directory
			fileInfo, err := os.Stat(filepath.Join(dataDir, requestedPath))
			if err != nil || !fileInfo.IsDir() {
				// Serve static files as the path does not map to a directory
				fileServer.ServeHTTP(w, r)
				return
			}

			// Serve the zip archive for the requested directory
			w.Header().Set("Content-Type", "application/zip")
			w.Header().Set("Content-Disposition", fmt.Sprintf("attachment; filename=\"%s.zip\"", requestedPath))

			err = createZipArchive(filepath.Join(dataDir, requestedPath), w)
			if err != nil {
				http.Error(w, "Error creating zip archive", http.StatusInternalServerError)
				return
			}
			return
		}

		// Serve static files
		fileServer.ServeHTTP(w, r)
	})))

	// Start the server on the specified host and port
	addr := host + ":" + port
	fmt.Println("Server is running on http://" + addr)
	err = http.ListenAndServe(addr, nil)
	if err != nil {
		fmt.Println("Error:", err)
	}
}
