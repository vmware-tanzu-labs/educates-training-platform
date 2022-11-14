// Copyright 2022 The Educates Authors.

package cmd

import (
	"bytes"
	"fmt"
	"path"
	"path/filepath"
	"strings"
	"text/template"

	composeloader "github.com/compose-spec/compose-go/loader"
	composetypes "github.com/compose-spec/compose-go/types"
	dockercommand "github.com/docker/cli/cli/command"
	"github.com/docker/compose/v2/cmd/compose"
	"github.com/docker/compose/v2/pkg/api"
	dockercompose "github.com/docker/compose/v2/pkg/compose"
	"github.com/pkg/errors"
	"github.com/spf13/cobra"
	"gopkg.in/yaml.v2"
	"k8s.io/apimachinery/pkg/apis/meta/v1/unstructured"
)

type DockerWorkshopExportOptions struct {
	Path         string
	Port         uint
	Repository   string
	RepositoryIP string
	Version      string
}

const containerScript = `exec bash -s << "EOF"
mkdir -p /opt/eduk8s/config
cat > /opt/eduk8s/config/workshop.yaml << "EOS"
{{ .WorkshopConfig -}}
EOS
{{ range $k, $v := .VendirFilesConfig -}}
{{ $off := inc $k -}}
cat > /opt/eduk8s/config/vendir-assets-{{ printf "%02d" $off }}.yaml << "EOS"
{{ $v -}}
EOS
{{ end -}}
exec start-container
EOF
`

func (o *DockerWorkshopExportOptions) Run(cmd *cobra.Command) error {
	var err error

	// If path not provided assume the current working directory. When loading
	// the workshop will then expect the workshop definition to reside in the
	// resources/workshop.yaml file under the directory, the same as if a
	// directory path was provided explicitly.

	if o.Path == "" {
		o.Path = "."
	}

	// Load the workshop definition. The path can be a HTTP/HTTPS URL for a
	// local file system path for a directory or file.

	var workshop *unstructured.Unstructured

	if workshop, err = loadWorkshopDefinition("", o.Path, "educates-cli"); err != nil {
		return err
	}

	// name := workshop.GetName()

	originalName := workshop.GetAnnotations()["training.educates.dev/workshop"]

	var workshopConfigData string
	var vendirFilesConfigData []string
	// var vendirPackagesConfigData string
	var workshopImageName string

	var workshopPortsConfig []composetypes.ServicePortConfig
	var workshopVolumesConfig []composetypes.ServiceVolumeConfig

	var workshopDockerVolumesConfig []composetypes.ServiceVolumeConfig

	var workshopEnvironment []string
	var workshopLabels map[string]string
	var workshopExtraHosts map[string]string

	var workshopComposeProject *composetypes.Project

	if workshopConfigData, err = generateWorkshopConfig(workshop); err != nil {
		return err
	}

	if vendirFilesConfigData, err = generateVendirFilesConfig(workshop, originalName, o.Repository); err != nil {
		return err
	}

	// if vendirPackagesConfigData, err = generateVendirPackagesConfig(workshop, originalName, o.Repository); err != nil {
	// 	return err
	// }

	if workshopImageName, err = generateWorkshopImageName(workshop, o.Repository, o.Version); err != nil {
		return err
	}

	if workshopPortsConfig, err = composetypes.ParsePortConfig(fmt.Sprintf("127.0.0.1:%d:10081", o.Port)); err != nil {
		return errors.Wrap(err, "unable to generate workshop ports config")
	}

	if workshopDockerVolumesConfig, err = generateWorkshopVolumeMounts(workshop); err != nil {
		return err
	}

	workshopVolumesConfig = append(workshopVolumesConfig, workshopDockerVolumesConfig...)

	if workshopEnvironment, err = generateWorkshopEnvironment(workshop, o.Repository, o.Port); err != nil {
		return err
	}

	if workshopLabels, err = generateWorkshopLabels(workshop, o.Port); err != nil {
		return err
	}

	if workshopExtraHosts, err = generateWorkshopExtraHosts(workshop, o.RepositoryIP); err != nil {
		return err
	}

	if workshopComposeProject, err = extractWorkshopComposeConfig(workshop); err != nil {
		return err
	}

	type TemplateInputs struct {
		WorkshopConfig       string
		VendirFilesConfig    []string
		VendirPackagesConfig string
	}

	inputs := TemplateInputs{
		WorkshopConfig:    workshopConfigData,
		VendirFilesConfig: vendirFilesConfigData,
		// VendirPackagesConfig: vendirPackagesConfigData,
	}

	funcMap := template.FuncMap{
		"inc": func(i int) int {
			return i + 1
		},
	}

	containerScriptTemplate, err := template.New("entrypoint").Funcs(funcMap).Parse(containerScript)

	if err != nil {
		return errors.Wrap(err, "not able to parse container script template")
	}

	var containerScriptData bytes.Buffer

	err = containerScriptTemplate.Execute(&containerScriptData, inputs)

	if err != nil {
		return errors.Wrap(err, "not able to generate container script")
	}

	workshopServiceConfig := composetypes.ServiceConfig{
		Name:        "workshop",
		Image:       workshopImageName,
		Command:     composetypes.ShellCommand([]string{"bash", "-c", containerScriptData.String()}),
		User:        "1001:0",
		Ports:       workshopPortsConfig,
		Volumes:     workshopVolumesConfig,
		Environment: composetypes.NewMappingWithEquals(workshopEnvironment),
		Labels:      composetypes.Labels(workshopLabels),
		ExtraHosts:  composetypes.HostsList(workshopExtraHosts),
		DependsOn:   composetypes.DependsOnConfig{},
		Networks: map[string]*composetypes.ServiceNetworkConfig{
			"default":  {},
			"educates": {},
		},
	}

	workshopServices := []composetypes.ServiceConfig{workshopServiceConfig}

	if workshopComposeProject != nil {
		for _, extraService := range workshopComposeProject.Services {
			extraService.Ports = []composetypes.ServicePortConfig{}

			workshopServices = append(workshopServices, extraService)

			workshopServiceConfig.DependsOn[extraService.Name] = composetypes.ServiceDependency{
				Condition: composetypes.ServiceConditionStarted,
			}
		}
	}

	composeConfig := composetypes.Project{
		Name:     originalName,
		Services: workshopServices,
		Networks: composetypes.Networks{
			"educates": {External: composetypes.External{External: true}},
		},
		Volumes: workshopComposeProject.Volumes,
	}

	composeConfigBytes, err := yaml.Marshal(&composeConfig)

	if err != nil {
		return errors.Wrap(err, "failed to generate compose config")
	}

	composeConfigString := string(composeConfigBytes)

	fmt.Println(composeConfigString)

	dockerCli, err := dockercommand.NewDockerCli()

	if err != nil {
		return errors.Wrap(err, "failed to initialize docker cli")
	}

	serviceProxy := api.NewServiceProxy().WithService(dockercompose.NewComposeService(dockerCli))

	composeCmd := compose.RootCommand(dockerCli, serviceProxy)

	fmt.Println(composeCmd)

	return nil
}

func (p *ProjectInfo) NewDockerWorkshopExportCmd() *cobra.Command {
	var o DockerWorkshopExportOptions

	var c = &cobra.Command{
		Args:  cobra.NoArgs,
		Use:   "export",
		Short: "Export workshop compose config",
		RunE:  func(cmd *cobra.Command, _ []string) error { return o.Run(cmd) },
	}

	c.Flags().StringVarP(
		&o.Path,
		"file",
		"f",
		".",
		"path to local workshop directory, definition file, or URL for workshop definition file",
	)
	c.Flags().UintVarP(
		&o.Port,
		"port",
		"p",
		10081,
		"port to host the workshop on localhost",
	)
	c.Flags().StringVar(
		&o.Repository,
		"repository",
		"registry.docker.local:5000",
		"the address of the image repository",
	)
	c.Flags().StringVar(
		&o.RepositoryIP,
		"repository-ip",
		"",
		"the IP address of the image repository host",
	)
	c.Flags().StringVar(
		&o.Version,
		"version",
		p.Version,
		"version of workshop base images to be used",
	)

	return c
}

func generateWorkshopConfig(workshop *unstructured.Unstructured) (string, error) {
	applicationsConfig, _, _ := unstructured.NestedMap(workshop.Object, "spec", "session", "applications")
	ingressesConfig, _, _ := unstructured.NestedSlice(workshop.Object, "spec", "session", "ingresses")
	dashboardsConfig, _, _ := unstructured.NestedSlice(workshop.Object, "spec", "session", "dashboards")

	workshopConfig := map[string]interface{}{
		"spec": map[string]interface{}{
			"session": map[string]interface{}{
				"applications": applicationsConfig,
				"ingresses":    ingressesConfig,
				"dashboards":   dashboardsConfig,
			},
		},
	}

	workshopConfigData, err := yaml.Marshal(&workshopConfig)

	if err != nil {
		return "", errors.Wrap(err, "failed to generate workshop config")
	}

	return string(workshopConfigData), nil
}

func generateVendirFilesConfig(workshop *unstructured.Unstructured, name string, repository string) ([]string, error) {
	var vendirConfigs []string

	filesItems, found, _ := unstructured.NestedSlice(workshop.Object, "spec", "workshop", "files")

	if found && len(filesItems) != 0 {
		for _, filesItem := range filesItems {
			directoriesConfig := []map[string]interface{}{}

			tmpPath, found := filesItem.(map[string]interface{})["path"]

			var filesItemPath string

			if found {
				filesItemPath = tmpPath.(string)
			} else {
				filesItemPath = "."
			}

			filesItemPath = filepath.Clean(path.Join("/opt/assets/files", filesItemPath))

			filesItem.(map[string]interface{})["path"] = "."

			directoriesConfig = append(directoriesConfig, map[string]interface{}{
				"path":     filesItemPath,
				"contents": []interface{}{filesItem},
			})

			vendirConfig := map[string]interface{}{
				"apiVersion":  "vendir.k14s.io/v1alpha1",
				"kind":        "Config",
				"directories": directoriesConfig,
			}

			vendirConfigBytes, err := yaml.Marshal(&vendirConfig)

			if err != nil {
				return []string{}, errors.Wrap(err, "failed to generate vendir config")
			}

			vendirConfigString := string(vendirConfigBytes)

			vendirConfigString = strings.ReplaceAll(vendirConfigString, "$(image_repository)", repository)
			vendirConfigString = strings.ReplaceAll(vendirConfigString, "$(workshop_name)", name)

			vendirConfigs = append(vendirConfigs, vendirConfigString)
		}
	}

	return vendirConfigs, nil
}

func generateVendirPackagesConfig(workshop *unstructured.Unstructured, name string, repository string) (string, error) {
	var vendirConfigString string

	packagesItems, found, _ := unstructured.NestedSlice(workshop.Object, "spec", "workshop", "packages")

	if found && len(packagesItems) != 0 {
		directoriesConfig := []map[string]interface{}{}

		for _, packagesItem := range packagesItems {
			tmpPackagesItem := packagesItem.(map[string]interface{})

			tmpName, found := tmpPackagesItem["name"]

			if !found {
				continue
			}

			packagesItemPath := filepath.Clean(path.Join("/opt/packages", tmpName.(string)))

			tmpPackagesFilesItem := tmpPackagesItem["files"]

			packagesFilesItem := tmpPackagesFilesItem.([]interface{})

			for _, tmpEntry := range packagesFilesItem {
				entry := tmpEntry.(map[string]interface{})

				_, found = entry["path"]

				if !found {
					entry["path"] = "."
				}
			}

			directoriesConfig = append(directoriesConfig, map[string]interface{}{
				"path":     packagesItemPath,
				"contents": packagesFilesItem,
			})

		}

		vendirConfig := map[string]interface{}{
			"apiVersion":  "vendir.k14s.io/v1alpha1",
			"kind":        "Config",
			"directories": directoriesConfig,
		}

		vendirConfigBytes, err := yaml.Marshal(&vendirConfig)

		if err != nil {
			return "", errors.Wrap(err, "failed to generate vendir config")
		}

		vendirConfigString = string(vendirConfigBytes)

		vendirConfigString = strings.ReplaceAll(vendirConfigString, "$(image_repository)", repository)
		vendirConfigString = strings.ReplaceAll(vendirConfigString, "$(workshop_name)", name)
	}

	return vendirConfigString, nil
}

func generateWorkshopImageName(workshop *unstructured.Unstructured, repository string, version string) (string, error) {
	image, found, err := unstructured.NestedString(workshop.Object, "spec", "workshop", "image")

	if err != nil {
		return "", errors.Wrapf(err, "unable to parse workshop definition")
	}

	if !found || image == "" {
		image = "base-environment:*"
	}

	defaultImageVersion := strings.TrimSpace(version)

	image = strings.ReplaceAll(image, "base-environment:*", fmt.Sprintf("ghcr.io/vmware-tanzu-labs/educates-base-environment:%s", defaultImageVersion))
	image = strings.ReplaceAll(image, "jdk8-environment:*", fmt.Sprintf("ghcr.io/vmware-tanzu-labs/educates-jdk8-environment:%s", defaultImageVersion))
	image = strings.ReplaceAll(image, "jdk11-environment:*", fmt.Sprintf("ghcr.io/vmware-tanzu-labs/educates-jdk11-environment:%s", defaultImageVersion))
	image = strings.ReplaceAll(image, "jdk17-environment:*", fmt.Sprintf("ghcr.io/vmware-tanzu-labs/educates-jdk17-environment:%s", defaultImageVersion))
	image = strings.ReplaceAll(image, "conda-environment:*", fmt.Sprintf("ghcr.io/vmware-tanzu-labs/educates-conda-environment:%s", defaultImageVersion))

	image = strings.ReplaceAll(image, "$(image_repository)", repository)

	return image, nil
}

func generateWorkshopVolumeMounts(workshop *unstructured.Unstructured) ([]composetypes.ServiceVolumeConfig, error) {
	var filesMounts []composetypes.ServiceVolumeConfig

	dockerEnabled, found, _ := unstructured.NestedBool(workshop.Object, "spec", "session", "applications", "docker", "enabled")

	if found && dockerEnabled {
		extraServices, _, _ := unstructured.NestedMap(workshop.Object, "spec", "session", "applications", "docker", "compose")

		socketEnabledDefault := true

		if len(extraServices) != 0 {
			socketEnabledDefault = false
		}

		socketEnabled, found, _ := unstructured.NestedBool(workshop.Object, "spec", "session", "applications", "docker", "socket", "enabled")

		if !found {
			socketEnabled = socketEnabledDefault
		}

		if socketEnabled {
			filesMounts = append(filesMounts, composetypes.ServiceVolumeConfig{
				Type: "bind",
				// XXX May need to detect when docker desktop to use raw socket alias.
				Source:   "/var/run/docker.sock.raw",
				Target:   "/var/run/docker/docker.sock",
				ReadOnly: true,
			})
		}
	}

	return filesMounts, nil
}

func generateWorkshopEnvironment(workshop *unstructured.Unstructured, repository string, port uint) ([]string, error) {
	return []string{
		"INGRESS_PROTOCOL=http",
		"INGRESS_DOMAIN=127-0-0-1.nip.io",
		fmt.Sprintf("INGRESS_PORT_SUFFIX=:%d", port),
		// fmt.Sprintf("SESSION_NAMESPACE=%s", name),
		fmt.Sprintf("IMAGE_REPOSITORY=%s", repository),
	}, nil
}

func generateWorkshopLabels(workshop *unstructured.Unstructured, port uint) (map[string]string, error) {
	labels := workshop.GetAnnotations()

	labels["training.educates.dev/url"] = fmt.Sprintf("http://workshop.127-0-0-1.nip.io:%d", port)

	return labels, nil
}

func generateWorkshopExtraHosts(workshop *unstructured.Unstructured, registryIP string) (map[string]string, error) {
	hosts := map[string]string{}

	if registryIP != "" {
		hosts["registry.docker.local"] = registryIP
	}

	return hosts, nil
}

func extractWorkshopComposeConfig(workshop *unstructured.Unstructured) (*composetypes.Project, error) {
	composeConfigObj, found, _ := unstructured.NestedMap(workshop.Object, "spec", "session", "applications", "docker", "compose")

	if found {
		composeConfigObjBytes, err := yaml.Marshal(&composeConfigObj)

		if err != nil {
			return nil, errors.Wrap(err, "unable to parse workshop docker compose config")
		}

		configFiles := composetypes.ConfigFile{
			Content: composeConfigObjBytes,
		}

		composeConfigDetails := composetypes.ConfigDetails{
			ConfigFiles: []composetypes.ConfigFile{configFiles},
		}

		return composeloader.Load(composeConfigDetails, func(options *composeloader.Options) {
			options.SkipConsistencyCheck = true
			options.SkipNormalization = true
			options.ResolvePaths = false
		})
	}

	return nil, nil
}
