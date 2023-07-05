// Copyright 2022-2023 The Educates Authors.

package renderer

import (
	"context"
	"embed"
	"encoding/json"
	"fmt"
	"io/ioutil"
	"log"
	"net/http"
	"net/http/httputil"
	"net/url"
	"os"
	"os/exec"
	"os/signal"
	"path"
	"path/filepath"
	"strconv"
	"strings"
	"sync"
	"syscall"
	"time"

	"github.com/pkg/errors"
	"github.com/vmware-tanzu-labs/educates-training-platform/client-programs/pkg/cluster"
	"gopkg.in/yaml.v2"
	k8serrors "k8s.io/apimachinery/pkg/api/errors"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/apis/meta/v1/unstructured"
	"k8s.io/apimachinery/pkg/runtime/schema"
)

//go:embed all:files/*
var hugoFiles embed.FS

func copyFiles(fs embed.FS, src string, dst string) error {
	files, err := hugoFiles.ReadDir(src)

	if err != nil {
		return errors.Wrapf(err, "unable to open files directory %q", src)
	}

	for _, file := range files {
		srcFile := path.Join(src, file.Name())
		dstFile := path.Join(dst, file.Name())

		if file.IsDir() {
			if err = os.MkdirAll(dstFile, 0775); err != nil {
				return errors.Wrapf(err, "unable to create workshop directory %q", dstFile)
			}

			if err = copyFiles(fs, srcFile, dstFile); err != nil {
				return err
			}
		} else {
			input, err := fs.ReadFile(srcFile)

			if err != nil {
				return errors.Wrapf(err, "unable to open source file %q", srcFile)
			}

			err = ioutil.WriteFile(dstFile, input, 0644)

			if err != nil {
				return errors.Wrapf(err, "unable to create source file %q", dstFile)
			}
		}
	}

	return nil
}

type WorkshopParamsConfig struct {
	Name    string   `yaml:"name"`
	Value   string   `yaml:"value"`
	Aliases []string `yaml:"aliases,omitempty"`
}

type WorkshopPathConfig struct {
	Title       string                 `yaml:"title,omitempty"`
	Description string                 `yaml:"description,omitempty"`
	Params      []WorkshopParamsConfig `yaml:"params,omitempty"`
	Steps       []string               `yaml:"steps,omitempty"`
}

type WorkshopModuleConfig struct {
	Title    string `yaml:"title"`
	Path     string `yaml:"path"`
	PrevPage string `yaml:"prev_page"`
	NextPage string `yaml:"next_page"`
	Step     int    `yaml:"step"`
}

type WorkshopPathwaysConfig struct {
	Default string                          `yaml:"default,omitempty"`
	Paths   map[string]WorkshopPathConfig   `yaml:"paths,omitempty"`
	Modules map[string]WorkshopModuleConfig `yaml:"modules,omitempty"`
}

type WorkshopConfig struct {
	Pathways WorkshopPathwaysConfig `yaml:"pathways,omitempty"`
	Params   []WorkshopParamsConfig `yaml:"params,omitempty"`
}

var workshopSessionResource = schema.GroupVersionResource{Group: "training.educates.dev", Version: "v1beta1", Resource: "workshopsessions"}

func fetchWorkshopSessionAndValidate(kubeconfig string, environment string, session string) (string, string, error) {
	// Returns session URL, config password and error.

	var err error

	clusterConfig := cluster.NewClusterConfig(kubeconfig)

	dynamicClient, err := clusterConfig.GetDynamicClient()

	if err != nil {
		return "", "", errors.Wrapf(err, "unable to create Kubernetes client")
	}

	workshopSessionClient := dynamicClient.Resource(workshopSessionResource)

	workshopSession, err := workshopSessionClient.Get(context.TODO(), session, metav1.GetOptions{})

	if k8serrors.IsNotFound(err) {
		return "", "", errors.New("no workshop session can be found")
	}

	linkedEnvironment, _, _ := unstructured.NestedString(workshopSession.Object, "spec", "environment", "name")

	if linkedEnvironment != environment {
		return "", "", errors.New("workshop environment name linked to workshop session")
	}

	password, _, _ := unstructured.NestedString(workshopSession.Object, "spec", "session", "config", "password")
	sessionURL, _, _ := unstructured.NestedString(workshopSession.Object, "status", "educates", "url")

	if password == "" {
		return "", "", errors.New("cannot determine config password for session")
	}

	if sessionURL == "" {
		return "", "", errors.New("cannot determine url for accessing workshop session")
	}

	return sessionURL, password, nil
}

func fetchSessionVariables(sessionURL string, password string) (map[string]string, error) {
	var err error

	params := make(map[string]string)

	url := fmt.Sprintf("%s/config/variables", sessionURL)

	req, err := http.NewRequest("GET", url, nil)

	if err != nil {
		return params, errors.Wrapf(err, "cannot construct request to query workshop session config")
	}

	q := req.URL.Query()
	q.Add("token", password)
	req.URL.RawQuery = q.Encode()

	res, err := http.DefaultClient.Do(req)

	if err != nil {
		return params, errors.Wrapf(err, "cannot query workshop session config")
	}

	if res.StatusCode != 200 {
		return params, errors.New("unexpected failure querying workshop session config")
	}

	resBody, err := ioutil.ReadAll(res.Body)

	if err != nil {
		return params, errors.Wrapf(err, "failed to read workshop session config")
	}

	err = json.Unmarshal(resBody, &params)

	if err != nil {
		return params, errors.Wrapf(err, "unable to unpack workshop session parameters")
	}

	return params, nil
}

func generateHugoConfiguration(source string, target string, params map[string]string, sessionURL string) error {
	var err error

	// Read user workshop config with details of any pathways.

	sourceConfigPath := filepath.Join(source, "config.yaml")

	sourceConfigData, err := os.ReadFile(sourceConfigPath)

	activeModules := map[string]*WorkshopModuleConfig{}

	if err == nil {
		// Assume file doesn't exist if had an error and skip it.

		sourceConfig := WorkshopConfig{}

		err = yaml.Unmarshal(sourceConfigData, &sourceConfig)

		if err != nil {
			return errors.Wrapf(err, "unable to unpack workshop config")
		}

		// Use the pathway name calculated from the workshop session and if
		// not defined fallback to the using default pathway name if specified.

		pathwayName := params["pathway_name"]

		if pathwayName == "" {
			if len(sourceConfig.Pathways.Paths) != 0 {
				pathwayName = sourceConfig.Pathways.Default
			}
		}

		pathway, pathwayExists := sourceConfig.Pathways.Paths[pathwayName]

		if pathwayName != "" && pathwayExists && len(pathway.Steps) != 0 {
			modules := sourceConfig.Pathways.Modules

			firstPage := ""
			prevPage := ""

			for index, step := range pathway.Steps {
				if firstPage == "" {
					firstPage = step
				}

				module, moduleExists := modules[step]

				if !moduleExists {
					module = WorkshopModuleConfig{}
				}

				module.Path = step

				if prevPage != "" {
					module.PrevPage = prevPage
					activeModules[prevPage].NextPage = step
				} else {
					module.PrevPage = ""
				}

				module.NextPage = ""
				module.Step = index + 1

				prevPage = step

				activeModules[step] = &module
			}

			params["__first_page__"] = firstPage
		}
	}

	type HugoConfig struct {
		BaseURL string                 `yaml:"baseURL"`
		Params  map[string]interface{} `yaml:"params"`
	}

	config := HugoConfig{Params: make(map[string]interface{})}

	config.BaseURL = fmt.Sprintf("%s/workshop/content/", sessionURL)

	for paramName, paramValue := range params {
		config.Params[paramName] = paramValue
	}

	config.Params["__modules__"] = activeModules

	configData, err := yaml.Marshal(config)

	if err != nil {
		return errors.Wrapf(err, "unable to marshal hugo configuration")
	}

	if err != nil {
		return errors.Wrapf(err, "unable to create hugo files directory")
	}

	targetFile := filepath.Join(target, "hugo.yaml")
	workingFile := filepath.Join(target, "hugo.yaml.tmp")

	configFile, err := os.Create(workingFile)

	if err != nil {
		return errors.Wrapf(err, "unable to create working hugo config file")
	}

	_, err = configFile.Write(configData)

	if err != nil {
		return errors.Wrapf(err, "unable to write working hugo config file")
	}

	configFile.Close()

	err = os.Rename(workingFile, targetFile)

	if err != nil {
		return errors.Wrapf(err, "unable to update hugo config file")
	}

	return nil
}

func startHugoServer(source string, tempDir string, port int, sessionURL string) error {
	// Run this in a go routine.

	wsPort := 80

	if strings.HasPrefix(sessionURL, "https://") {
		wsPort = 443
	}

	commandArgs := []string{
		"server",
		"--log",
		"--verbose",
		"--verboseLog",
		"--source", source,
		"--port", strconv.Itoa(port),
		"--disableFastRender",
		"--liveReloadPort", fmt.Sprintf("%d", wsPort),
		"--config", filepath.Join(tempDir, "hugo.yaml"),
		"--themesDir", filepath.Join(tempDir, "themes"),
		"--theme", "educates",
		"--watch",
	}

	commandPath, err := exec.LookPath("hugo")

	if err != nil {
		return errors.Wrapf(err, "unable to find hugo program")
	}

	command := exec.Command(commandPath, commandArgs...)

	stdout, err := command.StdoutPipe()
	command.Stderr = command.Stdout

	if err != nil {
		return errors.Wrapf(err, "unable to create command output pipe")
	}

	if err = command.Start(); err != nil {
		return errors.Wrapf(err, "failed to execute hugo program")
	}

	for {
		tmp := make([]byte, 1024)
		_, err := stdout.Read(tmp)
		fmt.Print(string(tmp))
		if err != nil {
			break
		}
	}

	return nil
}

func populateTemporaryDirectory() (string, error) {
	tempDir, err := ioutil.TempDir("", "educates")

	if err != nil {
		return "", errors.Wrapf(err, "unable to create hugo files directory")
	}

	err = copyFiles(hugoFiles, "files", tempDir)

	if err != nil {
		return "", errors.Wrapf(err, "failed to copy hugo files")
	}

	return tempDir, nil
}

func RunHugoServer(source string, kubeconfig string, environment string, proxyPort int, hugoPort int) error {
	var err error
	var tempDir string

	// First create directory to hold unpacked files for Hugo to use.

	if tempDir, err = populateTemporaryDirectory(); err != nil {
		return err
	}

	defer os.RemoveAll(tempDir)

	// Also catch signals so we can try and cleanup temporary directory.

	c := make(chan os.Signal)

	signal.Notify(c, os.Interrupt, syscall.SIGTERM)
	go func() {
		<-c
		fmt.Println("Cleaning up...")
		os.RemoveAll(tempDir)
		os.Exit(1)
	}()

	// Now need to create a mini HTTP server to handle requests.

	var serverDetailsLock sync.Mutex

	var hugoStarted bool = false
	var lastSessionName = ""

	requestHandler := func(w http.ResponseWriter, r *http.Request) {
		// Request must provide session name via header.

		sessionName := r.Header.Get("X-Session-Name")

		if sessionName == "" {
			w.WriteHeader(http.StatusBadRequest)
			w.Write([]byte("400 - Session name required"))

			return
		}

		// If session name not the same as last seen, regenerate files.

		serverDetailsLock.Lock()

		if sessionName != lastSessionName {
			// First validate that can access workshop session.

			sessionURL, password, err := fetchWorkshopSessionAndValidate(kubeconfig, environment, sessionName)

			if err != nil {
				fmt.Println("Error validating workshop session:", err)

				w.WriteHeader(http.StatusInternalServerError)
				w.Write([]byte("500 - Unable to validate workshop session"))

				serverDetailsLock.Unlock()

				return
			}

			// Then fetch back the session variables for the workshop session.

			params, err := fetchSessionVariables(sessionURL, password)

			if err != nil {
				fmt.Println("Error fetching session variables:", err)

				w.WriteHeader(http.StatusInternalServerError)
				w.Write([]byte("500 - Unable to fetch workshop session config"))

				serverDetailsLock.Unlock()

				return
			}

			// Generate (or regenerate) the Hugo configuration.

			err = generateHugoConfiguration(source, tempDir, params, sessionURL)

			if err != nil {
				fmt.Println("Unable to generate Hugo configuration:", err)

				w.WriteHeader(http.StatusInternalServerError)
				w.Write([]byte("500 - Unable to generate server configuration"))

				serverDetailsLock.Unlock()

				return
			}

			// If Hugo server is not already running it, start it. Add short
			// delays to give the Hugo server time to start or reload.

			if !hugoStarted {
				fmt.Println("Starting Hugo server")

				go startHugoServer(source, tempDir, hugoPort, sessionURL)

				time.Sleep(4 * time.Second)

				hugoStarted = true
			} else {
				time.Sleep(2 * time.Second)
			}

			// Update last seen session name.

			lastSessionName = sessionName
		}

		serverDetailsLock.Unlock()

		hugoServerURL := fmt.Sprintf("http://localhost:%d", hugoPort)
		target, _ := url.Parse(hugoServerURL)

		proxy := httputil.NewSingleHostReverseProxy(target)

		proxyPass := func(res http.ResponseWriter, req *http.Request) {
			proxy.ServeHTTP(w, req)
		}

		proxyPass(w, r)
	}

	http.HandleFunc("/workshop/content/", requestHandler)

	portString := fmt.Sprintf("0.0.0.0:%d", proxyPort)

	fmt.Println("Proxy listening on:", portString)

	log.Fatal(http.ListenAndServe(portString, nil))

	return nil
}
