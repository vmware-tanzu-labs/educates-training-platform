package diagnostics

import (
	"bytes"
	"context"
	"encoding/base64"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"net/url"
	"os"
	"path/filepath"
	"strings"

	"github.com/pkg/errors"
	"github.com/vmware-tanzu-labs/educates-training-platform/client-programs/pkg/cluster"
	"github.com/vmware-tanzu-labs/educates-training-platform/client-programs/pkg/types"
	v1 "k8s.io/api/core/v1"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/apis/meta/v1/unstructured"
	"k8s.io/apimachinery/pkg/runtime/schema"
	"k8s.io/cli-runtime/pkg/printers"
)

var workshopResource = schema.GroupVersionResource{Group: "training.educates.dev", Version: "v1beta1", Resource: "workshops"}
var trainingportalResource = schema.GroupVersionResource{Group: "training.educates.dev", Version: "v1beta1", Resource: "trainingportals"}
var workshopsessionsResource = schema.GroupVersionResource{Group: "training.educates.dev", Version: "v1beta1", Resource: "workshopsessions"}
var workshoprequestsResource = schema.GroupVersionResource{Group: "training.educates.dev", Version: "v1beta1", Resource: "workshoprequests"}
var workshopenvironmentsResource = schema.GroupVersionResource{Group: "training.educates.dev", Version: "v1beta1", Resource: "workshopenvironments"}
var workshopallocationsResource = schema.GroupVersionResource{Group: "training.educates.dev", Version: "v1beta1", Resource: "workshopallocations"}
var secretcopierResource = schema.GroupVersionResource{Group: "secrets.educates.dev", Version: "v1beta1", Resource: "secretcopiers"}
var secretinjectorsResource = schema.GroupVersionResource{Group: "secrets.educates.dev", Version: "v1beta1", Resource: "secretinjectors"}
var secretexportersResource = schema.GroupVersionResource{Group: "secrets.educates.dev", Version: "v1beta1", Resource: "secretexporters"}
var secretimportersResource = schema.GroupVersionResource{Group: "secrets.educates.dev", Version: "v1beta1", Resource: "secretimporters"}

type ClusterDiagnosticsFetcher struct {
	clusterConfig *cluster.ClusterConfig
	tempDir       string
	verbose       bool
}

func (c *ClusterDiagnosticsFetcher) getEducatesNamespaces(fileName string) error {
	client, err := c.clusterConfig.GetClient()
	if err != nil {
		return err
	}

	namespaces, err := client.CoreV1().Namespaces().List(context.TODO(), metav1.ListOptions{
		// LabelSelector: "training.educates.dev/component",
	})
	if err != nil {
		return err
	}

	newFile, err := os.Create(filepath.Join(c.tempDir, fileName))
	if err != nil {
		return err
	}
	defer newFile.Close()

	y := printers.YAMLPrinter{}
	for _, object := range namespaces.Items {
		object.SetManagedFields(nil) // Remove managedFields from the object
		// We need to add the GroupVersionKind to the object, as it is not set by default. See: https://github.com/kubernetes-sigs/controller-runtime/issues/1517
		object.GetObjectKind().SetGroupVersionKind(schema.GroupVersionKind{Group: "", Version: "v1", Kind: "Namespace"})
		if err := y.PrintObj(&object, newFile); err != nil {
			return err
		}
	}

	if c.verbose {
		fmt.Printf("Educates namespaces saved in file: %v\n", fileName)
	}

	return nil
}

// TODO: Print events in a more human readable format
func (c *ClusterDiagnosticsFetcher) getEducatesNamespacesEvents(fileName string) error {
	client, err := c.clusterConfig.GetClient()
	if err != nil {
		return err
	}

	namespaces, err := client.CoreV1().Namespaces().List(context.TODO(), metav1.ListOptions{})
	if err != nil {
		return err
	}

	newFile, err := os.Create(filepath.Join(c.tempDir, fileName))
	if err != nil {
		return err
	}
	defer newFile.Close()

	y := printers.YAMLPrinter{}
	for _, namespace := range namespaces.Items {
		if !strings.HasPrefix(namespace.Labels["kubernetes.io/metadata.name"], "educates") {
			continue
		}
		events, err := client.CoreV1().Events(namespace.Name).List(context.TODO(), metav1.ListOptions{
			// LabelSelector: "training.educates.dev/component",
		})
		for _, object := range events.Items {
			object.SetManagedFields(nil) // Remove managedFields from the object
			// We need to add the GroupVersionKind to the object, as it is not set by default. See: https://github.com/kubernetes-sigs/controller-runtime/issues/1517
			object.GetObjectKind().SetGroupVersionKind(schema.GroupVersionKind{Group: "events.k8s.io", Version: "v1", Kind: "Event"})
			if err := y.PrintObj(&object, newFile); err != nil {
				return err
			}
		}
		if err != nil {
			return err
		}
	}
	if c.verbose {
		fmt.Printf("Educates namespaces events saved in file: %v\n", fileName)
	}

	return nil
}

func (c *ClusterDiagnosticsFetcher) fetchDynamicallyResources(res schema.GroupVersionResource, fileName string) error {
	dynamicClient, err := c.clusterConfig.GetDynamicClient()
	if err != nil {
		return err
	}
	dynClient := dynamicClient.Resource(res)

	objectList, err := dynClient.List(context.TODO(), metav1.ListOptions{})
	if err != nil {
		return err
	}

	newFile, err := os.Create(filepath.Join(c.tempDir, fileName))
	if err != nil {
		return err
	}
	defer newFile.Close()

	y := printers.YAMLPrinter{}
	for _, object := range objectList.Items {
		object.SetManagedFields(nil) // Remove managedFields from the object
		if err := y.PrintObj(&object, newFile); err != nil {
			return err
		}
	}

	if c.verbose {
		fmt.Printf("Educates %v saved in file: %v\n", res.Resource, fileName)
	}

	return nil
}

func (c *ClusterDiagnosticsFetcher) fetchLogsForDeployment(labelSelector, namespaceSelector, fileNamePattern string) error {
	client, err := c.clusterConfig.GetClient()
	if err != nil {
		return err
	}
	// Create an array of strings to store the namespaces
	var namespacesList []string
	if strings.Contains(namespaceSelector, "=") {
		namespaces, err := client.CoreV1().Namespaces().List(context.TODO(), metav1.ListOptions{
			LabelSelector: namespaceSelector,
		})
		if err != nil {
			return err
		}
		for _, namespace := range namespaces.Items {
			namespacesList = append(namespacesList, namespace.Name)
		}
	} else {
		namespacesList = strings.Split(namespaceSelector, ",")
	}

	for _, namespaceName := range namespacesList {
		pods, err := client.CoreV1().Pods(namespaceName).List(context.TODO(), metav1.ListOptions{
			LabelSelector: labelSelector,
		})
		if err != nil {
			return err
		}

		if strings.Contains(fileNamePattern, "%v") {
			fileNamePattern = fmt.Sprintf(fileNamePattern, namespaceName)
		}

		logFile, err := os.Create(filepath.Join(c.tempDir, fileNamePattern))
		if err != nil {
			return err
		}
		defer logFile.Close()

		for _, pod := range pods.Items {
			req := client.CoreV1().Pods(pod.Namespace).GetLogs(pod.Name, &v1.PodLogOptions{})
			podLogs, err := req.Stream(context.TODO())
			if err != nil {
				return err
			}
			defer podLogs.Close()

			_, err = io.Copy(logFile, podLogs)
			if err != nil {
				return err
			}

			if c.verbose {
				fmt.Printf("Educates related logs saved in file: %v\n", fileNamePattern)
			}
		}
	}

	return nil
}

func (c *ClusterDiagnosticsFetcher) fetchTrainingPortalDetailsAtRest(fileNamePattern string) error {
	dynamicClient, err := c.clusterConfig.GetDynamicClient()
	if err != nil {
		return err
	}
	dynClient := dynamicClient.Resource(trainingportalResource)
	trainingPortals, err := dynClient.List(context.TODO(), metav1.ListOptions{})
	if err != nil {
		return err
	}
	// Iterate over the training portals and get the details of the workshop sessions
	for _, trainingPortal := range trainingPortals.Items {
		// trainingPortalName := trainingPortal.GetName()

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

		listEnvironmentsResult := &types.WorkshopsCatalogResponse{}

		err = json.NewDecoder(res.Body).Decode(listEnvironmentsResult)
		if err != nil {
			return errors.Wrap(err, "failed to decode response from training portal")
		}

		if strings.Contains(fileNamePattern, "%v") {
			fileNamePattern = fmt.Sprintf(fileNamePattern, trainingPortal.GetName())
		}
		newFile, err := os.Create(filepath.Join(c.tempDir, fileNamePattern))
		if err != nil {
			return err
		}
		defer newFile.Close()

		// Pretty print in json format listEnvironmentsResult
		prettyListEnvironmentsResult, err := json.MarshalIndent(listEnvironmentsResult, "", "  ")
		if err != nil {
			return err
		}
		// print into newFile
		_, err = newFile.Write(prettyListEnvironmentsResult)
		if err != nil {
			return err
		}

		if c.verbose {
			fmt.Printf("Educates trainingportal details at rest saved in file: %v\n", fileNamePattern)
		}

	}
	return nil
}
