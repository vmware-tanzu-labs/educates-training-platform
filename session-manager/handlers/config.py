import os
import yaml

from .helpers import lookup

config_values = {}

if os.path.exists("/opt/app-root/config/values.yaml"):
    with open("/opt/app-root/config/values.yaml") as fp:
        config_values = yaml.load(fp, Loader=yaml.Loader)

OPERATOR_NAMESPACE = lookup(config_values, "namespace.name", "educates")

if os.path.exists("/var/run/secrets/kubernetes.io/serviceaccount/namespace"):
    with open("/var/run/secrets/kubernetes.io/serviceaccount/namespace") as fp:
        OPERATOR_NAMESPACE = fp.read().strip()

OPERATOR_API_GROUP = lookup(config_values, "operatorApiGroup", "eduk8s.io")

RESOURCE_STATUS_KEY = lookup(config_values, "resourceStatusKey", "educates")
RESOURCE_NAME_PREFIX = lookup(config_values, "resourceNamePrefix", "educates")

IMAGE_REPOSITORY = lookup(config_values, "imageRepository.host")

if IMAGE_REPOSITORY:
    if lookup(config_values, "imageRepository.namespace"):
        IMAGE_REPOSITORY = f"{IMAGE_REPOSITORY}/" + lookup(
            config_values, "imageRepository.namespace"
        )
else:
    IMAGE_REPOSITORY = "registry.default.svc.cluster.local:5001"
