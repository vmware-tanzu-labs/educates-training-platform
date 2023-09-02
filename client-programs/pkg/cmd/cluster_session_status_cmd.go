package cmd

import (
	"context"
	"encoding/base64"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"net/url"
	"strings"

	"github.com/pkg/errors"
	"github.com/spf13/cobra"
	"github.com/vmware-tanzu-labs/educates-training-platform/client-programs/pkg/cluster"
	k8serrors "k8s.io/apimachinery/pkg/api/errors"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/apis/meta/v1/unstructured"
)

type ClusterSessionStatusOptions struct {
	Kubeconfig string
	Portal     string
	Name       string
}

func (o *ClusterSessionStatusOptions) Run() error {
	var err error

	clusterConfig := cluster.NewClusterConfig(o.Kubeconfig)

	dynamicClient, err := clusterConfig.GetDynamicClient()

	if err != nil {
		return errors.Wrapf(err, "unable to create Kubernetes client")
	}

	trainingPortalClient := dynamicClient.Resource(trainingPortalResource)

	trainingPortal, err := trainingPortalClient.Get(context.TODO(), o.Portal, metav1.GetOptions{})

	if k8serrors.IsNotFound(err) {
		fmt.Println("No session found.")
		return nil
	}

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
		return errors.Wrapf(err, "malformed request for training portal")
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

	req, err = http.NewRequest("GET", fmt.Sprintf("%s/workshops/session/%s/schedule/", portalUrl, o.Name), nil)

	if err != nil {
		return errors.Wrapf(err, "malformed request for training portal")
	}

	req.Header.Add("Authorization", fmt.Sprintf("Bearer %s", auth.AccessToken))

	res, err = http.DefaultClient.Do(req)

	if err != nil {
		return errors.Wrapf(err, "cannot connect to training portal")
	}

	if res.StatusCode == 400 || res.StatusCode == 404 {
		fmt.Println("No session found.")
		return nil
	}

	if res.StatusCode != 200 {
		return errors.New("cannot get session status from training portal")
	}

	resBody, err = io.ReadAll(res.Body)

	if err != nil {
		return errors.Wrapf(err, "cannot read response to status request")
	}

	type SessionDetails struct {
		Started    string `json:"started"`
		Expires    string `json:"expires"`
		Expiring   bool   `json:"expiring"`
		Countdown  int    `json:"countdown"`
		Extendable bool   `json:"extendable"`
		Status     string `json:"status"`
	}

	var details SessionDetails

	err = json.Unmarshal(resBody, &details)

	if err != nil {
		return errors.Wrapf(err, "cannot decode session details")
	}

	fmt.Println("Started:", details.Started)
	fmt.Println("Expires:", details.Expires)
	fmt.Println("Expiring:", details.Expiring)
	fmt.Println("Countdown:", details.Countdown)
	fmt.Println("Extendable:", details.Extendable)
	fmt.Println("Status:", details.Status)

	return nil
}

func (p *ProjectInfo) NewClusterSessionStatusCmd() *cobra.Command {
	var o ClusterSessionStatusOptions

	var c = &cobra.Command{
		Args:  cobra.ExactArgs(1),
		Use:   "status",
		Short: "Output status of session",
		RunE:  func(_ *cobra.Command, args []string) error { o.Name = args[0]; return o.Run() },
	}

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
		"name of the training portal",
	)

	return c
}
