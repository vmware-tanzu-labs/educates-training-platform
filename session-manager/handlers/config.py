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
