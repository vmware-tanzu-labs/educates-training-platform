package cmd

import (
	"context"
	"encoding/json"
	"fmt"
	"net"
	"net/http"
	"os"
	"os/signal"
	"regexp"
	"syscall"

	"github.com/pkg/errors"
	"github.com/spf13/cobra"
)

type DockerExtensionBackendOptions struct {
	Socket string
}

type DockerWorkshopsBackend struct {
	Manager DockerWorkshopsManager
}

func NewDockerWorkshopsBackend() DockerWorkshopsBackend {
	return DockerWorkshopsBackend{
		Manager: NewDockerWorkshopsManager(),
	}
}

func (b *DockerWorkshopsBackend) ListWorkhops(w http.ResponseWriter, r *http.Request) {
	workshops, err := b.Manager.ListWorkhops()

	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	jsonData, err := json.Marshal(workshops)

	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")

	w.WriteHeader(http.StatusOK)
	w.Write(jsonData)
}

func (b *DockerWorkshopsBackend) DeleteWorkshop(w http.ResponseWriter, r *http.Request) {
	queryParams := r.URL.Query()

	name := queryParams.Get("name")

	if name == "" {
		http.Error(w, "workshop session name required", http.StatusBadRequest)
		return
	}

	err := b.Manager.DeleteWorkshop(name, os.Stdout, os.Stderr)

	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	workshop := DockerWorkshopDetails{
		Session: name,
		Status:  "Stopped",
	}

	jsonData, err := json.Marshal(workshop)

	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")

	w.WriteHeader(http.StatusOK)
	w.Write(jsonData)
}

func (o *DockerExtensionBackendOptions) Run(p *ProjectInfo) error {
	if o.Socket == "" {
		return errors.New("invalid socket for HTTP server")
	}

	router := http.NewServeMux()

	versionHandler := func(w http.ResponseWriter, r *http.Request) {
		fmt.Fprintln(w, p.Version)
	}

	router.HandleFunc("/version", versionHandler)

	backend := NewDockerWorkshopsBackend()

	router.HandleFunc("/workshop/list", backend.ListWorkhops)
	router.HandleFunc("/workshop/delete", backend.DeleteWorkshop)

	server := http.Server{
		Handler: router,
	}

	// The socket string can either be of the form host:nnn, or it can be a file
	// system path (absolute or relative). In the first case we start up a
	// normal HTTP server accepting connections over an INET socket connection.
	// In the second case connections will be accepted over a UNIX socket.

	inetRegexPattern := `^([a-zA-Z0-9.-]+):(\d+)$`

	match, err := regexp.MatchString(inetRegexPattern, o.Socket)

	if err != nil {
		return errors.Wrap(err, "failed to perform regex match on socket")
	}

	var listener net.Listener

	if match {
		listener, err = net.Listen("tcp", o.Socket)

		if err != nil {
			return errors.Wrap(err, "unable to create INET HTTP server socket")
		}
	} else {
		listener, err = net.Listen("unix", o.Socket)

		if err != nil {
			return errors.Wrap(err, "unable to create UNIX HTTP server socket")
		}

		defer os.Remove(o.Socket)
	}

	defer listener.Close()

	go func() {
		server.Serve(listener)
	}()

	sigChan := make(chan os.Signal, 1)
	signal.Notify(sigChan, os.Interrupt, syscall.SIGTERM)
	<-sigChan

	err = server.Shutdown(context.TODO())

	if err != nil {
		return errors.Wrap(err, "failed to shutdown HTTP server")
	}

	return nil
}

func (p *ProjectInfo) NewDockerExtensionBackendCmd() *cobra.Command {
	var o DockerExtensionBackendOptions

	var c = &cobra.Command{
		Args:  cobra.NoArgs,
		Use:   "backend",
		Short: "Docker desktop extension backend",
		RunE:  func(_ *cobra.Command, _ []string) error { return o.Run(p) },
	}

	c.Flags().StringVar(
		&o.Socket,
		"socket",
		"",
		"socket to listen on for HTTP server connections",
	)

	cobra.MarkFlagRequired(c.Flags(), "socket")

	return c
}
