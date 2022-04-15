import os
import yaml
import logging
import string
import random

from .helpers import xget

logger = logging.getLogger("educates")

config_values = {}

if os.path.exists("/opt/app-root/config/values.yaml"):
    with open("/opt/app-root/config/values.yaml") as fp:
        config_values = yaml.load(fp, Loader=yaml.Loader)

OPERATOR_NAMESPACE = xget(config_values, "operator.namespace", "educates")

if os.path.exists("/var/run/secrets/kubernetes.io/serviceaccount/namespace"):
    with open("/var/run/secrets/kubernetes.io/serviceaccount/namespace") as fp:
        OPERATOR_NAMESPACE = fp.read().strip()

OPERATOR_API_GROUP = xget(config_values, "operator.apiGroup", "eduk8s.io")

OPERATOR_STATUS_KEY = xget(config_values, "operator.statusKey", "educates")
OPERATOR_NAME_PREFIX = xget(config_values, "operator.namePrefix", "educates")

IMAGE_REPOSITORY_HOST = xget(config_values, "imageRepository.host")
IMAGE_REPOSITORY_NAMESPACE = xget(config_values, "imageRepository.namespace")

if IMAGE_REPOSITORY_HOST:
    if IMAGE_REPOSITORY_NAMESPACE:
        IMAGE_REPOSITORY = f"{IMAGE_REPOSITORY_HOST}/{IMAGE_REPOSITORY_NAMESPACE}"
    else:
        IMAGE_REPOSITORY = IMAGE_REPOSITORY_HOST
else:
    IMAGE_REPOSITORY = "registry.default.svc.cluster.local:5001"

INGRESS_DOMAIN = xget(config_values, "clusterIngress.domain", "educates-local-dev.io")
INGRESS_CLASS = xget(config_values, "clusterIngress.class", "")

INGRESS_SECRET = xget(config_values, "clusterIngress.tlsCertificateRef.name")

if not INGRESS_SECRET:
    tls_certficate = xget(config_values, "clusterIngres.tlsCertificate", {})
    if (
        tls_certficate
        and tls_certficate.get("tls.crt")
        and tls_certficate.get("tls.key")
    ):
        INGRESS_SECRET = f"{INGRESS_DOMAIN}-tls"

INGRESS_PROTOCOL = xget(config_values, "clusterIngress.protocol", "")

if not INGRESS_PROTOCOL:
    if INGRESS_SECRET:
        INGRESS_PROTOCOL = "https"
    else:
        INGRESS_PROTOCOL = "http"

CLUSTER_STORAGE_CLASS = xget(config_values, "clusterStorage.class", "")
CLUSTER_STORAGE_USER = xget(config_values, "clusterStorage.user")
CLUSTER_STORAGE_GROUP = xget(config_values, "clusterStorage.group", 0)

DOCKERD_MTU = xget(config_values, "dockerDaemon.networkMTU", 1400)
DOCKERD_ROOTLESS = xget(config_values, "dockerDaemon.rootless", True)
DOCKERD_PRIVILEGED = xget(config_values, "dockerDaemon.privileged", True)
DOCKERD_MIRROR_REMOTE = xget(config_values, "dockerDaemon.proxyCache.remoteURL")
DOCKERD_MIRROR_USERNAME = xget(config_values, "dockerDaemon.proxyCache.username", "")
DOCKERD_MIRROR_PASSWORD = xget(config_values, "dockerDaemon.proxyCache.password", "")

NETWORK_BLOCKCIDRS = xget(config_values, "clusterNetwork.blockCIDRs", [])

GOOGLE_TRACKING_ID = xget(config_values, "workshopAnalytics.google.trackingId")

THEME_DASHBOARD_SCRIPT = xget(
    config_values, "websiteStyling.workshopDashboard.script", ""
)
THEME_DASHBOARD_STYLE = xget(
    config_values, "websiteStyling.workshopDashboard.style", ""
)
THEME_WORKSHOP_SCRIPT = xget(
    config_values, "websiteStyling.workshopInstructions.script", ""
)
THEME_WORKSHOP_STYLE = xget(
    config_values, "websiteStyling.workshopInstructions.style", ""
)
THEME_PORTAL_SCRIPT = xget(config_values, "websiteStyling.trainingPortal.script", "")
THEME_PORTAL_STYLE = xget(config_values, "websiteStyling.trainingPortal.style", "")


def generate_password(length):
    characters = string.ascii_letters + string.digits
    return "".join(random.sample(characters, length))


PORTAL_ADMIN_USERNAME = xget(
    config_values, "trainingPortal.credentials.admin.username", "educates"
)
PORTAL_ADMIN_PASSWORD = xget(
    config_values, "trainingPortal.credentials.admin.password", generate_password(32)
)
PORTAL_ROBOT_USERNAME = xget(
    config_values, "trainingPortal.credentials.robot.username", "robot@educates"
)
PORTAL_ROBOT_PASSWORD = xget(
    config_values, "trainingPortal.credentials.robot.password", generate_password(32)
)
PORTAL_ROBOT_CLIENT_ID = xget(
    config_values, "trainingPortal.clients.robot.id", generate_password(32)
)
PORTAL_ROBOT_CLIENT_SECRET = xget(
    config_values, "trainingPortal.clients.robot.secret", generate_password(32)
)


def image_reference(name):
    version = xget(config_values, "version", "latest")
    image = f"{IMAGE_REPOSITORY}/educates-{name}:{version}"
    image_versions = xget(config_values, "imageVersions", [])
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