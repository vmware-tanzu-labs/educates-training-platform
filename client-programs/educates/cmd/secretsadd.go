/*
Copyright © 2022 The Educates Authors.
*/
package cmd

import (
	"encoding/base64"
	"encoding/json"
	"fmt"
	"os"
	"path"
	"regexp"

	"github.com/adrg/xdg"
	"github.com/pkg/errors"
	"github.com/spf13/cobra"
	apiv1 "k8s.io/api/core/v1"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"sigs.k8s.io/yaml"
)

func NewSecretsAddCmd() *cobra.Command {
	var secretsAddCmd = &cobra.Command{
		Args:  cobra.NoArgs,
		Use:   "add",
		Short: "Add secret to the cache",
	}

	secretsAddCmd.AddCommand(
		NewSecretsAddDockerRegistryCmd(),
		// NewSecretsAddGenericCmd(),
		NewSecretsAddTlsCmd(),
	)

	return secretsAddCmd
}

type SecretsAddTlsOptions struct {
	CertFile      string
	KeyFile       string
	IngressDomain string
}

func (o *SecretsAddTlsOptions) Run(name string) error {
	var err error
	var matched bool

	if matched, err = regexp.MatchString("^[a-z0-9]([.a-z0-9-]+)?[a-z0-9]$", name); err != nil {
		return errors.Wrapf(err, "regex match on secret name failed")
	}

	if !matched {
		return errors.New("invalid secret name")
	}

	var certificateFileData []byte
	var certificateKeyFileData []byte

	if o.CertFile != "" {
		certificateFileData, err = os.ReadFile(o.CertFile)

		if err != nil {
			return errors.Wrapf(err, "failed to read certificate file %s", o.CertFile)
		}
	}

	if o.KeyFile != "" {
		certificateKeyFileData, err = os.ReadFile(o.KeyFile)

		if err != nil {
			return errors.Wrapf(err, "failed to read certificate key file %s", o.KeyFile)
		}
	}

	secret := &apiv1.Secret{
		ObjectMeta: metav1.ObjectMeta{
			Name:        name,
			Annotations: map[string]string{},
		},
		Type: "kubernetes.io/tls",
		Data: map[string][]byte{
			"tls.crt": certificateFileData,
			"tls.key": certificateKeyFileData,
		},
	}

	if o.IngressDomain != "" {
		secret.ObjectMeta.Annotations["training.educates.dev/domain"] = o.IngressDomain
	}

	secretData, err := json.MarshalIndent(&secret, "", "    ")

	if err != nil {
		return errors.Wrap(err, "failed to generate secret data")
	}

	secretData, err = yaml.JSONToYAML(secretData)

	if err != nil {
		return errors.Wrap(err, "failed to generate YAML data")
	}

	configFileDir := path.Join(xdg.DataHome, "educates")
	secretsCacheDir := path.Join(configFileDir, "secrets")

	err = os.MkdirAll(secretsCacheDir, os.ModePerm)

	if err != nil {
		return errors.Wrapf(err, "unable to create secrets cache directory")
	}

	secretFilePath := path.Join(secretsCacheDir, name+".yaml")

	secretFile, err := os.OpenFile(secretFilePath, os.O_RDWR|os.O_CREATE|os.O_TRUNC, os.ModePerm)

	if err != nil {
		return errors.Wrapf(err, "unable to create secret file %s", secretFile)
	}

	_, err = secretFile.Write(secretData)

	if err := secretFile.Close(); err != nil {
		return errors.Wrapf(err, "unable to close secret file %s", secretFile)
	}

	return nil
}

func NewSecretsAddTlsCmd() *cobra.Command {
	var o SecretsAddTlsOptions

	var c = &cobra.Command{
		Args:  cobra.ExactArgs(1),
		Use:   "tls NAME",
		Short: "Create a TLS secret",
		RunE:  func(_ *cobra.Command, args []string) error { return o.Run(args[0]) },
	}

	c.Flags().StringVar(
		&o.CertFile,
		"cert",
		"",
		"path to PEM encoded public key certificate",
	)
	c.Flags().StringVar(
		&o.KeyFile,
		"key",
		"",
		"path to private key associated with given certificate",
	)
	c.Flags().StringVar(
		&o.IngressDomain,
		"domain",
		"",
		"wildcard ingress domain matching certificate",
	)

	c.MarkFlagsRequiredTogether("cert", "key")

	return c
}

type SecretsAddDockerRegistryOptions struct {
	Server   string
	Username string
	Password string
	Email    string
}

func (o *SecretsAddDockerRegistryOptions) Run(name string) error {
	var err error
	var matched bool

	if matched, err = regexp.MatchString("^[a-z0-9]([.a-z0-9-]+)?[a-z0-9]$", name); err != nil {
		return errors.Wrapf(err, "regex match on secret name failed")
	}

	if !matched {
		return errors.New("invalid secret name")
	}

	authString := base64.StdEncoding.EncodeToString([]byte(fmt.Sprintf("%s:%s", o.Username, o.Password)))

	dockerConfig := map[string]interface{}{
		"auths": map[string]interface{}{
			o.Server: map[string]string{
				"username": o.Username,
				"password": o.Password,
				"email":    o.Email,
				"auth":     authString,
			},
		},
	}

	dockerConfigData, _ := json.Marshal(dockerConfig)

	secret := &apiv1.Secret{
		ObjectMeta: metav1.ObjectMeta{
			Name: name,
		},
		Type: "kubernetes.io/dockerconfigjson",
		Data: map[string][]byte{
			".dockerconfigjson": dockerConfigData,
		},
	}

	secretData, err := json.MarshalIndent(&secret, "", "    ")

	if err != nil {
		return errors.Wrap(err, "failed to generate secret data")
	}

	secretData, err = yaml.JSONToYAML(secretData)

	if err != nil {
		return errors.Wrap(err, "failed to generate YAML data")
	}

	configFileDir := path.Join(xdg.DataHome, "educates")
	secretsCacheDir := path.Join(configFileDir, "secrets")

	err = os.MkdirAll(secretsCacheDir, os.ModePerm)

	if err != nil {
		return errors.Wrapf(err, "unable to create secrets cache directory")
	}

	secretFilePath := path.Join(secretsCacheDir, name+".yaml")

	secretFile, err := os.OpenFile(secretFilePath, os.O_RDWR|os.O_CREATE|os.O_TRUNC, os.ModePerm)

	if err != nil {
		return errors.Wrapf(err, "unable to create secret file %s", secretFile)
	}

	_, err = secretFile.Write(secretData)

	if err := secretFile.Close(); err != nil {
		return errors.Wrapf(err, "unable to close secret file %s", secretFile)
	}

	return nil
}

func NewSecretsAddDockerRegistryCmd() *cobra.Command {
	var o SecretsAddDockerRegistryOptions

	var c = &cobra.Command{
		Args:  cobra.ExactArgs(1),
		Use:   "docker-registry NAME",
		Short: "Create a secret for use with a Docker registry",
		RunE:  func(_ *cobra.Command, args []string) error { return o.Run(args[0]) },
	}

	c.Flags().StringVar(
		&o.Server,
		"docker-server",
		"https://index.docker.io/v1/",
		"server location for docker registry",
	)
	c.Flags().StringVar(
		&o.Username,
		"docker-username",
		"",
		"username for docker registry authentication",
	)
	c.Flags().StringVar(
		&o.Password,
		"docker-password",
		"",
		"password for docker registry authentication",
	)
	c.Flags().StringVar(
		&o.Email,
		"docker-email",
		"",
		"email for docker registry",
	)

	c.MarkFlagsRequiredTogether("docker-username", "docker-password", "docker-email")

	return c
}

type SecretsAddGenericOptions struct {
	FileSources    []string
	LiteralSources []string
}

func (o *SecretsAddGenericOptions) Run(name string) error {
	return nil
}

func NewSecretsAddGenericCmd() *cobra.Command {
	var o SecretsAddGenericOptions

	var c = &cobra.Command{
		Args:  cobra.ExactArgs(1),
		Use:   "generic NAME",
		Short: "Create a secret from a local file, directory, or literal value",
		RunE:  func(_ *cobra.Command, args []string) error { return o.Run(args[0]) },
	}

	c.Flags().StringArrayVar(
		&o.FileSources,
		"from-file",
		[]string{},
		"Key files can be specified using their file path, in which case a default name will be given to them, or optionally with a name and file path, in which case the given name will be used. Specifying a directory will iterate each named file in the directory that is avalid secret key.",
	)
	c.Flags().StringArrayVar(
		&o.LiteralSources,
		"from-literal",
		[]string{},
		"Specify a key and literal value to insert in secret (i.e. mykey=somevalue)",
	)

	return c
}
