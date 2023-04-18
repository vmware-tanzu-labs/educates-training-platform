// Copyright 2022-2023 The Educates Authors.

package cmd

import (
	"bytes"
	"context"
	"encoding/base64"
	"encoding/json"
	"fmt"
	"io"
	"io/ioutil"
	"net/http"
	"net/url"
	"os/exec"
	"runtime"
	"strings"

	"github.com/joho/godotenv"
	"github.com/pkg/errors"
	"github.com/spf13/cobra"
	"github.com/vmware-tanzu-labs/educates-training-platform/client-programs/pkg/cluster"
	k8serrors "k8s.io/apimachinery/pkg/api/errors"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/apis/meta/v1/unstructured"
	"k8s.io/client-go/dynamic"
)

type ClusterWorkshopRequestOptions struct {
	Name        string
	Path        string
	Kubeconfig  string
	Portal      string
	Params      []string
	ParamFiles  []string
	ParamsFiles []string
}

func (o *ClusterWorkshopRequestOptions) Run() error {
	var err error

	var name = o.Name

	// Process parameters.

	params := map[string]string{}

	for _, item := range o.Params {
		parts := strings.SplitN(item, "=", 2)

		if len(parts) != 2 {
			return errors.Errorf("invalid parameter format %s", item)
		}

		params[parts[0]] = parts[1]
	}

	for _, item := range o.ParamFiles {
		parts := strings.SplitN(item, "=", 2)

		if len(parts) != 2 {
			return errors.Errorf("invalid parameter format %s", item)
		}

		content, err := ioutil.ReadFile(parts[1])

		if err != nil {
			return errors.Wrapf(err, "cannot read parameter data file %s", parts[1])
		}

		params[parts[0]] = string(content)
	}

	for _, item := range o.ParamsFiles {
		var paramsData map[string]string

		paramsData, err := godotenv.Read(item)

		if err != nil {
			return errors.Wrapf(err, "cannot read parameters data file %s", item)
		}

		for name, value := range paramsData {
			params[name] = value
		}
	}

	// Ensure have portal name.

	if o.Portal == "" {
		o.Portal = "educates-cli"
	}

	if name == "" {
		var path = o.Path

		// If path not provided assume the current working directory. When loading
		// the workshop will then expect the workshop definition to reside in the
		// resources/workshop.yaml file under the directory, the same as if a
		// directory path was provided explicitly.

		if path == "" {
			path = "."
		}

		// Load the workshop definition. The path can be a HTTP/HTTPS URL for a
		// local file system path for a directory or file.

		var workshop *unstructured.Unstructured

		if workshop, err = loadWorkshopDefinition(o.Name, path, o.Portal); err != nil {
			return err
		}

		name = workshop.GetName()
	}

	clusterConfig := cluster.NewClusterConfig(o.Kubeconfig)

	dynamicClient, err := clusterConfig.GetDynamicClient()

	if err != nil {
		return errors.Wrapf(err, "unable to create Kubernetes client")
	}

	// Request the workshop from the training portal.

	err = requestWorkshop(dynamicClient, name, o.Portal, params)

	if err != nil {
		return err
	}

	return nil
}

func (p *ProjectInfo) NewClusterWorkshopRequestCmd() *cobra.Command {
	var o ClusterWorkshopRequestOptions

	var c = &cobra.Command{
		Args:  cobra.NoArgs,
		Use:   "request",
		Short: "Request workshop in Kubernetes",
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
		"name to be used for training portal and workshop name prefixes",
	)
	c.Flags().StringArrayVarP(
		&o.Params,
		"param",
		"",
		[]string{},
		"set request parameter data value, as string, (format name=value)",
	)
	c.Flags().StringArrayVarP(
		&o.ParamFiles,
		"param-file",
		"",
		[]string{},
		"set request parameter data value, from file, (format name=path)",
	)
	c.Flags().StringArrayVarP(
		&o.ParamsFiles,
		"params-file",
		"",
		[]string{},
		"set request parameter data values from dotenv file",
	)

	return c
}

func requestWorkshop(client dynamic.Interface, name string, portal string, params map[string]string) error {

	trainingPortalClient := client.Resource(trainingPortalResource)

	trainingPortal, err := trainingPortalClient.Get(context.TODO(), portal, metav1.GetOptions{})

	if k8serrors.IsNotFound(err) {
		return errors.Wrap(err, "unable to retrieve training portal")
	}

	workshops, _, err := unstructured.NestedSlice(trainingPortal.Object, "spec", "workshops")

	if err != nil {
		return errors.Wrap(err, "unable to retrieve workshops from training portal")
	}

	var foundWorkshop = false

	for _, item := range workshops {
		object := item.(map[string]interface{})

		if object["name"] == name {
			foundWorkshop = true
		}
	}

	if !foundWorkshop {
		return errors.Wrapf(err, "unable to find workshop %s", name)
	}

	// Login to the training portal.

	portalUrl, _, _ := unstructured.NestedString(trainingPortal.Object, "status", "educates", "url")

	clientId, _, _ := unstructured.NestedString(trainingPortal.Object, "status", "educates", "clients", "robot", "id")
	clientSecret, _, _ := unstructured.NestedString(trainingPortal.Object, "status", "educates", "clients", "robot", "secret")

	username, _, _ := unstructured.NestedString(trainingPortal.Object, "status", "educates", "credentials", "robot", "username")
	password, _, _ := unstructured.NestedString(trainingPortal.Object, "status", "educates", "credentials", "robot", "password")

	if portalUrl == "" {
		return errors.New("invalid URL endpoint in training portal")
	}

	if username == "" || password == "" {
		return errors.New("invalid credentials in training portal")
	}

	form := url.Values{}

	form.Add("grant_type", "password")
	form.Add("username", username)
	form.Add("password", password)

	req, err := http.NewRequest("POST", fmt.Sprintf("%s/oauth2/token/", portalUrl), strings.NewReader(form.Encode()))

	if err != nil {
		return errors.Wrap(err, "malformed request for training portal")
	}

	credentials := base64.StdEncoding.EncodeToString([]byte(fmt.Sprintf("%s:%s", clientId, clientSecret)))

	req.Header.Add("Content-Type", "application/x-www-form-urlencoded")
	req.Header.Add("Authorization", fmt.Sprintf("Basic %s", credentials))

	res, err := http.DefaultClient.Do(req)

	if err != nil {
		return errors.Wrapf(err, "cannot connect to training portal")
	}

	if res.StatusCode != 200 {
		return errors.New("cannot login to training portal")
	}

	resBody, err := io.ReadAll(res.Body)

	if err != nil {
		return errors.Wrapf(err, "cannot read response to token request")
	}

	type AuthDetails struct {
		AccessToken  string `json:"access_token"`
		ExpiresIn    int    `json:"expires_in"`
		TokenType    string `json:"token_type"`
		Scope        string `json:"scope"`
		RefreshToken string `json:"refresh_token"`
	}

	var auth AuthDetails

	err = json.Unmarshal(resBody, &auth)

	if err != nil {
		return errors.Wrapf(err, "cannot decode auth details")
	}

	cleanupFunc := func() {
		form = url.Values{}

		form.Add("token", auth.AccessToken)
		form.Add("client_id", clientId)
		form.Add("client_secret", clientSecret)

		req, err := http.NewRequest("POST", fmt.Sprintf("%s/oauth2/revoke-token/", portalUrl), strings.NewReader(form.Encode()))

		if err == nil {
			req.Header.Add("Content-Type", "application/x-www-form-urlencoded")
			req.Header.Add("Authorization", fmt.Sprintf("Bearer %s", auth.AccessToken))

			_, _ = http.DefaultClient.Do(req)
		}
	}

	defer cleanupFunc()

	// Get the list of workshops so we can know which workshop environment
	// we need to request a workshop from.

	type WorkshopDetails struct {
		Name string `json:"name"`
	}

	type EnvironmentDetails struct {
		Name     string `json:"name"`
		State    string `json:"state"`
		Workshop WorkshopDetails
	}

	type ListEnvironmentsResponse struct {
		Environments []EnvironmentDetails
	}

	body := []byte("{}")

	requestURL := fmt.Sprintf("%s/workshops/catalog/environments", portalUrl)

	req, err = http.NewRequest("GET", requestURL, bytes.NewBuffer(body))

	if err != nil {
		return errors.Wrap(err, "malformed request for training portal")
	}

	req.Header.Add("Authorization", fmt.Sprintf("Bearer %s", auth.AccessToken))

	res, err = http.DefaultClient.Do(req)

	if err != nil {
		return errors.Wrap(err, "failed to request catalog from training portal")
	}

	defer res.Body.Close()

	if res.StatusCode != http.StatusOK {
		bodyBytes, err := io.ReadAll(res.Body)

		if err != nil {
			return errors.Wrap(err, "failed to read response body from training portal")
		}

		bodyString := string(bodyBytes)

		return errors.Errorf("request for catalog from training portal failed with error (%d, %s)", res.StatusCode, bodyString)
	}

	listEnvironmentsResult := &ListEnvironmentsResponse{}

	err = json.NewDecoder(res.Body).Decode(listEnvironmentsResult)

	if err != nil {
		return errors.Wrap(err, "failed to decode response from training portal")
	}

	// Work out the name of the workshop environment.

	environmentName := ""

	for _, item := range listEnvironmentsResult.Environments {
		if item.Workshop.Name == name && item.State == "RUNNING" {
			environmentName = item.Name
		}
	}

	if environmentName == "" {
		return errors.Errorf("cannot find workshop environment for workshop %s", name)
	}

	// Now request the workshop from the required workshop environment.

	type Parameter struct {
		Name  string `json:"name"`
		Value string `json:"value"`
	}

	type RequestWorkshopRequest struct {
		Parameters []Parameter `json:"parameters"`
	}

	type RequestWorkshopResponse struct {
		Name        string `json:"name"`
		User        string `json:"user"`
		URL         string `json:"url"`
		Workshop    string `json:"workshop"`
		Environment string `json:"environment"`
		Namespace   string `json:"namespace"`
	}

	inputData := RequestWorkshopRequest{
		Parameters: []Parameter{},
	}

	for name, value := range params {
		inputData.Parameters = append(inputData.Parameters, Parameter{name, value})
	}

	body, err = json.Marshal(inputData)

	if err != nil {
		return errors.Wrapf(err, "cannot marshal request parameters")
	}

	requestURL = fmt.Sprintf("%s/workshops/environment/%s/request/?index_url=%s", portalUrl, environmentName, url.QueryEscape(portalUrl))

	req, err = http.NewRequest("POST", requestURL, bytes.NewBuffer(body))

	if err != nil {
		return errors.Wrap(err, "malformed request for training portal")
	}

	req.Header.Add("Content-Type", "application/json")
	req.Header.Add("Authorization", fmt.Sprintf("Bearer %s", auth.AccessToken))

	res, err = http.DefaultClient.Do(req)

	if err != nil {
		return errors.Wrap(err, "failed to request workshop from training portal")
	}

	defer res.Body.Close()

	if res.StatusCode != http.StatusOK {
		bodyBytes, err := io.ReadAll(res.Body)

		if err != nil {
			return errors.Wrap(err, "failed to read response body from training portal")
		}

		bodyString := string(bodyBytes)

		return errors.Errorf("request for workshop from training portal failed with error (%d, %s)", res.StatusCode, bodyString)
	}

	requestWorkshopResult := &RequestWorkshopResponse{}

	err = json.NewDecoder(res.Body).Decode(requestWorkshopResult)

	if err != nil {
		return errors.Wrap(err, "failed to decode response from training portal")
	}

	workshopUrl := fmt.Sprintf("%s%s", portalUrl, requestWorkshopResult.URL)

	fmt.Println(workshopUrl)

	switch runtime.GOOS {
	case "linux":
		err = exec.Command("xdg-open", workshopUrl).Start()
	case "windows":
		err = exec.Command("rundll32", "url.dll,FileProtocolHandler", workshopUrl).Start()
	case "darwin":
		err = exec.Command("open", workshopUrl).Start()
	default:
		err = fmt.Errorf("unsupported platform")
	}

	if err != nil {
		return errors.Wrap(err, "unable to open web browser on workshop")
	}

	return nil
}
