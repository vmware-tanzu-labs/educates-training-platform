package cmd

import (
	"context"
	"fmt"
	"io"
	"net/http"
	"net/url"
	"os/exec"
	"runtime"
	"time"

	"github.com/pkg/errors"
	"github.com/spf13/cobra"
	"github.com/vmware-tanzu-labs/educates-training-platform/client-programs/pkg/cluster"
	k8serrors "k8s.io/apimachinery/pkg/api/errors"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/apis/meta/v1/unstructured"
)

type ClusterPortalOpenOptions struct {
	Kubeconfig string
	Admin      bool
	Portal     string
}

func (o *ClusterPortalOpenOptions) Run() error {
	var err error

	// Ensure have portal name.

	if o.Portal == "" {
		o.Portal = "educates-cli"
	}

	clusterConfig := cluster.NewClusterConfig(o.Kubeconfig)

	dynamicClient, err := clusterConfig.GetDynamicClient()

	if err != nil {
		return errors.Wrapf(err, "unable to create Kubernetes client")
	}

	trainingPortalClient := dynamicClient.Resource(trainingPortalResource)

	trainingPortal, err := trainingPortalClient.Get(context.TODO(), o.Portal, metav1.GetOptions{})

	if k8serrors.IsNotFound(err) {
		return errors.New("no workshops deployed")
	}

	targetUrl, found, _ := unstructured.NestedString(trainingPortal.Object, "status", "educates", "url")

	if !found {
		return errors.New("workshops not available")
	}

	rootUrl := targetUrl

	if o.Admin {
		targetUrl = targetUrl + "/admin"
	} else {
		password, _, _ := unstructured.NestedString(trainingPortal.Object, "spec", "portal", "password")

		if password != "" {
			values := url.Values{}
			values.Add("redirect_url", "/")
			values.Add("password", password)

			targetUrl = fmt.Sprintf("%s/workshops/access/?%s", targetUrl, values.Encode())
		}
	}

	for i := 1; i < 300; i++ {
		time.Sleep(time.Second)

		resp, err := http.Get(rootUrl)

		if err != nil || resp.StatusCode == 503 {
			continue
		}

		defer resp.Body.Close()
		io.ReadAll(resp.Body)

		break
	}

	switch runtime.GOOS {
	case "linux":
		err = exec.Command("xdg-open", targetUrl).Start()
	case "windows":
		err = exec.Command("rundll32", "url.dll,FileProtocolHandler", targetUrl).Start()
	case "darwin":
		err = exec.Command("open", targetUrl).Start()
	default:
		err = fmt.Errorf("unsupported platform")
	}

	if err != nil {
		return errors.Wrap(err, "unable to open web browser")
	}

	return nil
}

func (p *ProjectInfo) NewClusterPortalOpenCmd() *cobra.Command {
	var o ClusterPortalOpenOptions

	var c = &cobra.Command{
		Args:  cobra.NoArgs,
		Use:   "open",
		Short: "Browse portal in Kubernetes",
		RunE:  func(_ *cobra.Command, _ []string) error { return o.Run() },
	}

	c.Flags().StringVar(
		&o.Kubeconfig,
		"kubeconfig",
		"",
		"kubeconfig file to use instead of $KUBECONFIG or $HOME/.kube/config",
	)
	c.Flags().BoolVar(
		&o.Admin,
		"admin",
		false,
		"open URL for admin login instead of workshops catalog",
	)
	c.Flags().StringVarP(
		&o.Portal,
		"portal",
		"p",
		"educates-cli",
		"name to be used for training portal and workshop name prefixes",
	)

	return c
}
