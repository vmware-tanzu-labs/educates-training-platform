package educatesrestapi

import (
	"bytes"
	"context"
	"encoding/base64"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"net/url"
	"strings"

	"github.com/pkg/errors"
	"github.com/vmware-tanzu-labs/educates-training-platform/client-programs/pkg/cluster"
	k8serrors "k8s.io/apimachinery/pkg/api/errors"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/apis/meta/v1/unstructured"
	"k8s.io/apimachinery/pkg/runtime/schema"
)

type AuthDetails struct {
	AccessToken  string `json:"access_token"`
	ExpiresIn    int    `json:"expires_in"`
	TokenType    string `json:"token_type"`
	Scope        string `json:"scope"`
	RefreshToken string `json:"refresh_token"`
}

type WorkshopsCatalogRequesterApi interface {
	GetWorkshopsCatalog() (*WorkshopsCatalogResponse, error)
	Login() (func(), error)
	// Logout() error
}

type WorkshopsCatalogRequester struct {
	clusterConfig *cluster.ClusterConfig
	portal        string
	PortalUrl     string
	Auth          *AuthDetails
}

var _ WorkshopsCatalogRequesterApi = &WorkshopsCatalogRequester{}

func NewWorkshopsCatalogRequester(clusterConfig *cluster.ClusterConfig, portal string) *WorkshopsCatalogRequester {
	return &WorkshopsCatalogRequester{
		clusterConfig: clusterConfig,
		portal:        portal,
	}
}

func (c *WorkshopsCatalogRequester) GetWorkshopsCatalog() (*WorkshopsCatalogResponse, error) {
	body := []byte("{}")

	requestURL := fmt.Sprintf("%s/workshops/catalog/environments", c.PortalUrl)

	req, err := http.NewRequest("GET", requestURL, bytes.NewBuffer(body))

	if err != nil {
		return nil, errors.Wrap(err, "malformed request for training portal")
	}

	req.Header.Add("Authorization", fmt.Sprintf("Bearer %s", c.Auth.AccessToken))

	res, err := http.DefaultClient.Do(req)

	if err != nil {
		return nil, errors.Wrap(err, "failed to request catalog from training portal")
	}

	defer res.Body.Close()

	if res.StatusCode != http.StatusOK {
		bodyBytes, err := io.ReadAll(res.Body)

		if err != nil {
			return nil, errors.Wrap(err, "failed to read response body from training portal")
		}

		bodyString := string(bodyBytes)

		return nil, errors.Errorf("request for catalog from training portal failed with error (%d, %s)", res.StatusCode, bodyString)
	}

	listEnvironmentsResult := &WorkshopsCatalogResponse{}
	err = json.NewDecoder(res.Body).Decode(listEnvironmentsResult)
	if err != nil {
		return nil, errors.Wrap(err, "failed to decode response from training portal")
	}

	return listEnvironmentsResult, nil
}

func (c *WorkshopsCatalogRequester) Login() (func(), error) {
	var err error

	// clusterConfig := cluster.NewClusterConfig(o.Kubeconfig)

	if !cluster.IsClusterAvailable(c.clusterConfig) {
		return nil, errors.New("Cluster is not available")
	}

	dynamicClient, err := c.clusterConfig.GetDynamicClient()

	if err != nil {
		return nil, errors.Wrapf(err, "unable to create Kubernetes client")
	}

	trainingPortalClient := dynamicClient.Resource(schema.GroupVersionResource{Group: "training.educates.dev", Version: "v1beta1", Resource: "trainingportals"})

	trainingPortal, err := trainingPortalClient.Get(context.TODO(), c.portal, metav1.GetOptions{})

	if k8serrors.IsNotFound(err) {
		return nil, errors.New("No session found.")
	}

	c.PortalUrl, _, _ = unstructured.NestedString(trainingPortal.Object, "status", "educates", "url")

	clientId, _, _ := unstructured.NestedString(trainingPortal.Object, "status", "educates", "clients", "robot", "id")
	clientSecret, _, _ := unstructured.NestedString(trainingPortal.Object, "status", "educates", "clients", "robot", "secret")

	username, _, _ := unstructured.NestedString(trainingPortal.Object, "status", "educates", "credentials", "robot", "username")
	password, _, _ := unstructured.NestedString(trainingPortal.Object, "status", "educates", "credentials", "robot", "password")

	if c.PortalUrl == "" {
		return nil, errors.New("invalid URL endpoint in training portal")
	}

	if username == "" || password == "" {
		return nil, errors.New("invalid credentials in training portal")
	}

	form := url.Values{}

	form.Add("grant_type", "password")
	form.Add("username", username)
	form.Add("password", password)

	req, err := http.NewRequest("POST", fmt.Sprintf("%s/oauth2/token/", c.PortalUrl), strings.NewReader(form.Encode()))

	if err != nil {
		return nil, errors.Wrapf(err, "malformed request for training portal")
	}

	credentials := base64.StdEncoding.EncodeToString([]byte(fmt.Sprintf("%s:%s", clientId, clientSecret)))

	req.Header.Add("Content-Type", "application/x-www-form-urlencoded")
	req.Header.Add("Authorization", fmt.Sprintf("Basic %s", credentials))

	res, err := http.DefaultClient.Do(req)

	if err != nil {
		return nil, errors.Wrapf(err, "cannot connect to training portal")
	}

	if res.StatusCode != 200 {
		return nil, errors.New("cannot login to training portal")
	}

	resBody, err := io.ReadAll(res.Body)

	if err != nil {
		return nil, errors.Wrapf(err, "cannot read response to token request")
	}

	err = json.Unmarshal(resBody, &c.Auth)

	if err != nil {
		return nil, errors.Wrapf(err, "cannot decode auth details")
	}

	cleanupFunc := func() {
		form = url.Values{}

		form.Add("token", c.Auth.AccessToken)
		form.Add("client_id", clientId)
		form.Add("client_secret", clientSecret)

		req, err := http.NewRequest("POST", fmt.Sprintf("%s/oauth2/revoke-token/", c.PortalUrl), strings.NewReader(form.Encode()))

		if err == nil {
			req.Header.Add("Content-Type", "application/x-www-form-urlencoded")
			req.Header.Add("Authorization", fmt.Sprintf("Bearer %s", c.Auth.AccessToken))

			_, _ = http.DefaultClient.Do(req)
		}
	}

	return cleanupFunc, nil
}
