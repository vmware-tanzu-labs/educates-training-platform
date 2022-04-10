import os

OPERATOR_NAMESPACE = "educates"

if os.path.exists("/var/run/secrets/kubernetes.io/serviceaccount/namespace"):
    with open("/var/run/secrets/kubernetes.io/serviceaccount/namespace") as fp:
        OPERATOR_NAMESPACE = fp.read().strip()

OPERATOR_API_GROUP = os.environ.get("OPERATOR_API_GROUP", "eduk8s.io")

RESOURCE_STATUS_KEY = os.environ.get("RESOURCE_STATUS_KEY", "educates")
RESOURCE_NAME_PREFIX = os.environ.get("RESOURCE_NAME_PREFIX", "educates")
