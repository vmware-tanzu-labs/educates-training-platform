import os
import yaml
import logging
import string
import random

from .helpers import lookup

logger = logging.getLogger("educates")

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
    image_repository_namespace = lookup(config_values, "imageRepository.namespace")
    if image_repository_namespace:
        IMAGE_REPOSITORY = f"{IMAGE_REPOSITORY}/{image_repository_namespace}"
else:
    IMAGE_REPOSITORY = "registry.default.svc.cluster.local:5001"

INGRESS_DOMAIN = lookup(config_values, "ingressDomain", "educates-local-dev.io")
INGRESS_CLASS = lookup(config_values, "ingressClass", "")

INGRESS_SECRET = lookup(config_values, "tlsCertificateRef.name")

if not INGRESS_SECRET:
    tls_certficate = lookup(config_values, "tlsCertificate", {})
    if (
        tls_certficate
        and tls_certficate.get("tls.crt")
        and tls_certficate.get("tls.key")
    ):
        INGRESS_SECRET = f"{INGRESS_DOMAIN}-tls"

INGRESS_PROTOCOL = lookup(config_values, "ingressProtocol", "")

if not INGRESS_PROTOCOL:
    if INGRESS_SECRET:
        INGRESS_PROTOCOL = "https"
    else:
        INGRESS_PROTOCOL = "http"

CLUSTER_STORAGE_CLASS = lookup(config_values, "clusterStorage.class", "")
CLUSTER_STORAGE_USER = lookup(config_values, "clusterStorage.user")
CLUSTER_STORAGE_GROUP = lookup(config_values, "clusterStorage.group", 0)

DOCKERD_MTU = lookup(config_values, "dockerDaemon.networkMTU", 1400)
DOCKERD_ROOTLESS = lookup(config_values, "dockerDaemon.rootless", True)
DOCKERD_PRIVILEGED = lookup(config_values, "dockerDaemon.privileged", True)
DOCKERD_MIRROR_REMOTE = lookup(config_values, "dockerDaemon.proxyCache.remoteURL")
DOCKERD_MIRROR_USERNAME = lookup(config_values, "dockerDaemon.proxyCache.username", "")
DOCKERD_MIRROR_PASSWORD = lookup(config_values, "dockerDaemon.proxyCache.password", "")

NETWORK_BLOCKCIDRS = lookup(config_values, "clusterNetwork.blockCIDRs", [])

GOOGLE_TRACKING_ID = lookup(config_values, "workshopAnalytics.google.trackingId")

THEME_DASHBOARD_SCRIPT = lookup(
    config_values, "websiteStyling.workshopDashboard.script", ""
)
THEME_DASHBOARD_STYLE = lookup(
    config_values, "websiteStyling.workshopDashboard.style", ""
)
THEME_WORKSHOP_SCRIPT = lookup(
    config_values, "websiteStyling.workshopInstructions.script", ""
)
THEME_WORKSHOP_STYLE = lookup(
    config_values, "websiteStyling.workshopInstructions.style", ""
)
THEME_PORTAL_SCRIPT = lookup(config_values, "websiteStyling.trainingPortal.script", "")
THEME_PORTAL_STYLE = lookup(config_values, "websiteStyling.trainingPortal.style", "")


def generate_password(length):
    characters = string.ascii_letters + string.digits
    return "".join(random.sample(characters, length))


PORTAL_ADMIN_USERNAME = lookup(
    config_values, "trainingPortal.credentials.admin.username", "educates"
)
PORTAL_ADMIN_PASSWORD = lookup(
    config_values, "trainingPortal.credentials.admin.password", generate_password(32)
)
PORTAL_ROBOT_USERNAME = lookup(
    config_values, "trainingPortal.credentials.robot.username", "robot@educates"
)
PORTAL_ROBOT_PASSWORD = lookup(
    config_values, "trainingPortal.credentials.robot.password", generate_password(32)
)
PORTAL_ROBOT_CLIENT_ID = lookup(
    config_values, "trainingPortal.clients.robot.id", generate_password(32)
)
PORTAL_ROBOT_CLIENT_SECRET = lookup(
    config_values, "trainingPortal.clients.robot.secret", generate_password(32)
)


def image_reference(name):
    version = lookup(config_values, "version", "latest")
    image = f"{IMAGE_REPOSITORY}/educates-{name}:{version}"
    image_versions = lookup(config_values, "imageVersions", [])
    for item in image_versions:
        if item["name"] == name:
            image = item["image"]
            break
    return image


TRAINING_PORTAL_IMAGE = image_reference("training-portal")
DOCKER_IN_DOCKER_IMAGE = image_reference("docker-in-docker")
DOCKER_REGISTRY_IMAGE = image_reference("docker-registry")
BASE_ENVIRONMENT_IMAGE = image_reference("base-environment")
JDK8_ENVIRONMENT_IMAGE = image_reference("jdk8-environment")
JDK11_ENVIRONMENT_IMAGE = image_reference("jdk11-environment")
CONDA_ENVIRONMENT_IMAGE = image_reference("conda-environment")

workshop_images_table = {
    "base-environment:*": BASE_ENVIRONMENT_IMAGE,
    "jdk8-environment:*": JDK8_ENVIRONMENT_IMAGE,
    "jdk11-environment:*": JDK11_ENVIRONMENT_IMAGE,
    "conda-environment:*": CONDA_ENVIRONMENT_IMAGE,
}


def resolve_workshop_image(name):
    if name in workshop_images_table:
        return workshop_images_table[name]
    return name.replace("$(image_repository)", IMAGE_REPOSITORY)


for name, value in sorted(globals().items()):
    if name.isupper():
        logger.info(f"{name}: {repr(value)}")
