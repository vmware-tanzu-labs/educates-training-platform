// Copyright 2022-2023 The Educates Authors.

package cmd

import (
	"os"
	"path/filepath"

	"github.com/pkg/errors"
	"github.com/spf13/cobra"
	"k8s.io/apimachinery/pkg/apis/meta/v1/unstructured"

	"github.com/vmware-tanzu-labs/educates-training-platform/client-programs/pkg/renderer"
)

func calculateWorkshopRoot(path string) (string, error) {
	var err error

	// If path not provided assume the current working directory.

	if path == "" {
		path = "."
	}

	path = filepath.Clean(path)

	if path, err = filepath.Abs(path); err != nil {
		return "", errors.Wrap(err, "couldn't convert workshop directory to absolute path")
	}

	fileInfo, err := os.Stat(path)

	if err != nil || !fileInfo.IsDir() {
		return "", errors.New("workshop directory does not exist or path is not a directory")
	}

	return path, nil
}

func calculateWorkshopName(name string, path string, portal string) (string, error) {
	var err error

	if name == "" {
		// Load the workshop definition. The path can be a HTTP/HTTPS URL for a
		// local file system path for a directory or file.

		var workshop *unstructured.Unstructured

		if workshop, err = loadWorkshopDefinition(name, path, portal); err != nil {
			return "", err
		}

		name = workshop.GetName()
	}

	return name, nil
}

// func calculateEnvironmentName(client dynamic.Interface, name string, portal string) (string, error) {
// 	trainingPortalClient := client.Resource(trainingPortalResource)

// 	trainingPortal, err := trainingPortalClient.Get(context.TODO(), portal, metav1.GetOptions{})

// 	if k8serrors.IsNotFound(err) {
// 		return "", errors.Wrap(err, "unable to retrieve training portal")
// 	}

// 	workshops, _, err := unstructured.NestedSlice(trainingPortal.Object, "spec", "workshops")

// 	if err != nil {
// 		return "", errors.Wrap(err, "unable to retrieve workshops from training portal")
// 	}

// 	var foundWorkshop = false

// 	for _, item := range workshops {
// 		object := item.(map[string]interface{})

// 		if object["name"] == name {
// 			foundWorkshop = true
// 		}
// 	}

// 	if !foundWorkshop {
// 		return "", errors.Wrapf(err, "unable to find workshop %s", name)
// 	}

// 	// Login to the training portal.

// 	portalUrl, _, _ := unstructured.NestedString(trainingPortal.Object, "status", "educates", "url")

// 	clientId, _, _ := unstructured.NestedString(trainingPortal.Object, "status", "educates", "clients", "robot", "id")
// 	clientSecret, _, _ := unstructured.NestedString(trainingPortal.Object, "status", "educates", "clients", "robot", "secret")

// 	username, _, _ := unstructured.NestedString(trainingPortal.Object, "status", "educates", "credentials", "robot", "username")
// 	password, _, _ := unstructured.NestedString(trainingPortal.Object, "status", "educates", "credentials", "robot", "password")

// 	if portalUrl == "" {
// 		return "", errors.New("invalid URL endpoint in training portal")
// 	}

// 	if username == "" || password == "" {
// 		return "", errors.New("invalid credentials in training portal")
// 	}

// 	form := url.Values{}

// 	form.Add("grant_type", "password")
// 	form.Add("username", username)
// 	form.Add("password", password)

// 	req, err := http.NewRequest("POST", fmt.Sprintf("%s/oauth2/token/", portalUrl), strings.NewReader(form.Encode()))

// 	if err != nil {
// 		return "", errors.Wrap(err, "malformed request for training portal")
// 	}

// 	credentials := base64.StdEncoding.EncodeToString([]byte(fmt.Sprintf("%s:%s", clientId, clientSecret)))

// 	req.Header.Add("Content-Type", "application/x-www-form-urlencoded")
// 	req.Header.Add("Authorization", fmt.Sprintf("Basic %s", credentials))

// 	res, err := http.DefaultClient.Do(req)

// 	if err != nil {
// 		return "", errors.Wrapf(err, "cannot connect to training portal")
// 	}

// 	if res.StatusCode != 200 {
// 		return "", errors.New("cannot login to training portal")
// 	}

// 	resBody, err := io.ReadAll(res.Body)

// 	if err != nil {
// 		return "", errors.Wrapf(err, "cannot read response to token request")
// 	}

// 	type AuthDetails struct {
// 		AccessToken  string `json:"access_token"`
// 		ExpiresIn    int    `json:"expires_in"`
// 		TokenType    string `json:"token_type"`
// 		Scope        string `json:"scope"`
// 		RefreshToken string `json:"refresh_token"`
// 	}

// 	var auth AuthDetails

// 	err = json.Unmarshal(resBody, &auth)

// 	if err != nil {
// 		return "", errors.Wrapf(err, "cannot decode auth details")
// 	}

// 	cleanupFunc := func() {
// 		form = url.Values{}

// 		form.Add("token", auth.AccessToken)
// 		form.Add("client_id", clientId)
// 		form.Add("client_secret", clientSecret)

// 		req, err := http.NewRequest("POST", fmt.Sprintf("%s/oauth2/revoke-token/", portalUrl), strings.NewReader(form.Encode()))

// 		if err == nil {
// 			req.Header.Add("Content-Type", "application/x-www-form-urlencoded")
// 			req.Header.Add("Authorization", fmt.Sprintf("Bearer %s", auth.AccessToken))

// 			_, _ = http.DefaultClient.Do(req)
// 		}
// 	}

// 	defer cleanupFunc()

// 	// Get the list of workshops so we can know which workshop environment
// 	// we need to request a workshop from.

// 	type WorkshopDetails struct {
// 		Name string `json:"name"`
// 	}

// 	type EnvironmentDetails struct {
// 		Name     string `json:"name"`
// 		State    string `json:"state"`
// 		Workshop WorkshopDetails
// 	}

// 	type ListEnvironmentsResponse struct {
// 		Environments []EnvironmentDetails
// 	}

// 	body := []byte("{}")

// 	requestURL := fmt.Sprintf("%s/workshops/catalog/environments", portalUrl)

// 	req, err = http.NewRequest("GET", requestURL, bytes.NewBuffer(body))

// 	if err != nil {
// 		return "", errors.Wrap(err, "malformed request for training portal")
// 	}

// 	req.Header.Add("Authorization", fmt.Sprintf("Bearer %s", auth.AccessToken))

// 	res, err = http.DefaultClient.Do(req)

// 	if err != nil {
// 		return "", errors.Wrap(err, "failed to request catalog from training portal")
// 	}

// 	defer res.Body.Close()

// 	if res.StatusCode != http.StatusOK {
// 		bodyBytes, err := io.ReadAll(res.Body)

// 		if err != nil {
// 			return "", errors.Wrap(err, "failed to read response body from training portal")
// 		}

// 		bodyString := string(bodyBytes)

// 		return "", errors.Errorf("request for catalog from training portal failed with error (%d, %s)", res.StatusCode, bodyString)
// 	}

// 	listEnvironmentsResult := &ListEnvironmentsResponse{}

// 	err = json.NewDecoder(res.Body).Decode(listEnvironmentsResult)

// 	if err != nil {
// 		return "", errors.Wrap(err, "failed to decode response from training portal")
// 	}

// 	// Work out the name of the workshop environment.

// 	environmentName := ""

// 	for _, item := range listEnvironmentsResult.Environments {
// 		if item.Workshop.Name == name && item.State == "RUNNING" {
// 			environmentName = item.Name
// 		}
// 	}

// 	if environmentName == "" {
// 		return "", errors.Errorf("cannot find workshop environment for workshop %s", name)
// 	}

// 	return environmentName, nil
// }

type ClusterWorkshopServeOptions struct {
	Name       string
	Path       string
	Kubeconfig string
	// Environment string
	Portal    string
	ProxyPort int
	HugoPort  int
	Token     string
	Files     bool
}

func (o *ClusterWorkshopServeOptions) Run() error {
	var err error

	var name = o.Name
	var path = o.Path
	// var environment = o.Environment
	var portal = o.Portal

	// Ensure have portal name.

	if portal == "" {
		portal = "educates-cli"
	}

	// Calculate workshop root and name.

	if path, err = calculateWorkshopRoot(path); err != nil {
		return err
	}

	if name, err = calculateWorkshopName(name, path, portal); err != nil {
		return err
	}

	// Run the proxy server and Hugo server.

	return renderer.RunHugoServer(path, o.Kubeconfig, name, portal, o.ProxyPort, o.HugoPort, o.Token, o.Files)
}

func (p *ProjectInfo) NewClusterWorkshopServeCmd() *cobra.Command {
	var o ClusterWorkshopServeOptions

	var c = &cobra.Command{
		Args:  cobra.NoArgs,
		Use:   "server",
		Short: "Serve workshop from local system",
		RunE:  func(_ *cobra.Command, _ []string) error { return o.Run() },
	}

	c.Flags().StringVarP(
		&o.Name,
		"name",
		"n",
		"",
		"name to be used for the workshop definition, generated if not set",
	)
	c.Flags().StringVarP(
		&o.Path,
		"file",
		"f",
		".",
		"path to local workshop directory, definition file, or URL for workshop definition file",
	)
	c.Flags().StringVar(
		&o.Kubeconfig,
		"kubeconfig",
		"",
		"kubeconfig file to use instead of $KUBECONFIG or $HOME/.kube/config",
	)
	c.Flags().StringVarP(
		&o.Portal,
		"portal",
		"p",
		"educates-cli",
		"name of the training portal to lookup the workshop",
	)
	c.Flags().IntVar(
		&o.ProxyPort,
		"proxy-port",
		10081,
		"port on which the proxy service will listen",
	)
	c.Flags().IntVar(
		&o.HugoPort,
		"hugo-port",
		1313,
		"port on which the hugo server will listen",
	)
	c.Flags().StringVarP(
		&o.Token,
		"token",
		"",
		"",
		"access token for protecting access to server",
	)
	c.Flags().BoolVarP(
		&o.Files,
		"allow-files-download",
		"",
		false,
		"enable download of workshop files as tarball",
	)

	return c
}
