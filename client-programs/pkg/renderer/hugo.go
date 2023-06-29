// Copyright 2022-2023 The Educates Authors.

package renderer

import (
	"context"
	"embed"
	"encoding/json"
	"fmt"
	"io/ioutil"
	"net/http"
	"os"
	"os/exec"
	"path"
	"path/filepath"
	"strconv"
	"strings"

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

			// TODO Change permissions on files based on src.
		}
	}

	return nil
}

var workshopSessionResource = schema.GroupVersionResource{Group: "training.educates.dev", Version: "v1beta1", Resource: "workshopsessions"}

func RunHugoServer(source string, kubeconfig string, session string, port int) error {
	var err error

	clusterConfig := cluster.NewClusterConfig(kubeconfig)

	dynamicClient, err := clusterConfig.GetDynamicClient()

	if err != nil {
		return errors.Wrapf(err, "unable to create Kubernetes client")
	}

	workshopSessionClient := dynamicClient.Resource(workshopSessionResource)

	workshopSession, err := workshopSessionClient.Get(context.TODO(), session, metav1.GetOptions{})

	if k8serrors.IsNotFound(err) {
		return errors.New("no workshop session can be found")
	}

	password, _, _ := unstructured.NestedString(workshopSession.Object, "spec", "session", "config", "password")
	sessionURL, _, _ := unstructured.NestedString(workshopSession.Object, "status", "educates", "url")

	if password == "" {
		return errors.New("cannot determine config password for session")
	}

	if sessionURL == "" {
		return errors.New("cannot determine url for accessing workshop session")
	}

	url := fmt.Sprintf("%s/config/variables", sessionURL)

	req, err := http.NewRequest("GET", url, nil)

	if err != nil {
		return errors.Wrapf(err, "cannot construct request to query workshop session config")
	}

	q := req.URL.Query()
	q.Add("token", password)
	req.URL.RawQuery = q.Encode()

	res, err := http.DefaultClient.Do(req)

	if err != nil {
		return errors.Wrapf(err, "cannot query workshop session config")
	}

	if res.StatusCode != 200 {
		return errors.New("unexpected failure querying workshop session config")
	}

	resBody, err := ioutil.ReadAll(res.Body)

	if err != nil {
		return errors.Wrapf(err, "failed to read workshop session config")
	}

	params := map[string]string{}

	err = json.Unmarshal(resBody, &params)

	if err != nil {
		return errors.Wrapf(err, "unable to unpack workshop session parameters")
	}

	type HugoConfig struct {
		Params map[string]string `yaml:"params"`
	}

	config := HugoConfig{Params: params}

	configData, err := yaml.Marshal(config)

	if err != nil {
		return errors.Wrapf(err, "unable to marshal hugo configuration")
	}

	tempDir, err := ioutil.TempDir("", "educates")

	if err != nil {
		return errors.Wrapf(err, "unable to create hugo files directory")
	}

	defer os.RemoveAll(tempDir)

	err = copyFiles(hugoFiles, "files", tempDir)

	if err != nil {
		return errors.Wrapf(err, "failed to copy hugo files")
	}

	configFile, err := os.Create(filepath.Join(tempDir, "hugo.yaml"))

	if err != nil {
		return errors.Wrapf(err, "unable to create hugo config file")
	}

	configFile.Write(configData)

	configFile.Close()

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
		"--bind", "0.0.0.0",
		"--port", strconv.Itoa(port),
		"--liveReloadPort", fmt.Sprintf("%d", wsPort),
		"--config", filepath.Join(tempDir, "hugo.yaml"),
		"--themesDir", filepath.Join(tempDir, "themes"),
		"--baseURL", fmt.Sprintf("%s/workshop/content/", sessionURL),
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
