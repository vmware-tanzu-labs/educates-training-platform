"""Helper functions for working with kubeconfig files."""

import base64

from typing import Union

import kopf

# The kubeconfig file is a YAML file with the following structure:
#
# apiVersion: v1
# kind: Config
# clusters:
# - name: cluster-name
#   cluster:
#     server: https://kubernetes.default.svc
#     certificate-authority-data: <base64 encoded CA certificate>
# contexts:
# - name: cluster-name-context
#   context:
#     cluster: cluster-name
#     user: cluster-name-user
# current-context: cluster-name-context
# users:
# - name: cluster-name-user
#   user:
#     token: <service account token>


def create_kubeconfig_from_access_token_secret(
    directory: str,
    cluster_name: str,
    server_url: str = "https://kubernetes.default.svc",
) -> dict:
    """Creates a kubeconfig from mounted access token secret."""

    # The mounted directory is a volume created from the Kubernetes service
    # account token and CA certificate. We want to create a kubeconfig file that
    # uses these to access the Kubernetes API. First read the service account
    # token from the mounted directory.

    with open(f"{directory}/token", "r", encoding="utf-8") as token_file:
        token = token_file.read().strip()

    # Read the CA certificate from the mounted directory.

    with open(f"{directory}/ca.crt", "rb") as ca_file:
        ca_certificate_bytes = ca_file.read().strip()

    # Create the kubeconfig file.

    kubeconfig = {
        "apiVersion": "v1",
        "kind": "Config",
        "clusters": [
            {
                "name": cluster_name,
                "cluster": {
                    "server": server_url,
                    "certificate-authority-data": base64.b64encode(
                        ca_certificate_bytes
                    ).decode("utf-8"),
                },
            }
        ],
        "contexts": [
            {
                "name": f"{cluster_name}-context",
                "context": {
                    "cluster": cluster_name,
                    "user": f"{cluster_name}-user",
                },
            }
        ],
        "current-context": f"{cluster_name}-context",
        "users": [
            {
                "name": f"{cluster_name}-user",
                "user": {
                    "token": token,
                },
            }
        ],
    }

    return kubeconfig


def verify_kubeconfig_format(kubeconfig: dict) -> None:
    """Verifies that a kubeconfig file is well-formed."""

    # Verify the kubeconfig file has the correct structure.

    if (
        kubeconfig.get("apiVersion") != "v1"
        or kubeconfig.get("kind") != "Config"
        or not isinstance(kubeconfig.get("clusters"), list)
        or not isinstance(kubeconfig.get("contexts"), list)
        or not isinstance(kubeconfig.get("users"), list)
        or not isinstance(kubeconfig.get("current-context"), str)
    ):
        raise ValueError("Invalid kubeconfig file format.")

    for cluster in kubeconfig.get("clusters", []):
        if (
            not isinstance(cluster, dict)
            or not isinstance(cluster.get("name"), str)
            or not isinstance(cluster.get("cluster"), dict)
            or not isinstance(cluster["cluster"].get("server"), str)
            or not isinstance(cluster["cluster"].get("certificate-authority-data"), str)
        ):
            raise ValueError("Invalid kubeconfig file format.")

    for context in kubeconfig.get("contexts", []):
        if (
            not isinstance(context, dict)
            or not isinstance(context.get("name"), str)
            or not isinstance(context.get("context"), dict)
            or not isinstance(context["context"].get("cluster"), str)
            or not isinstance(context["context"].get("user"), str)
        ):
            raise ValueError("Invalid kubeconfig file format.")

    for user in kubeconfig.get("users", []):
        if (
            not isinstance(user, dict)
            or not isinstance(user.get("name"), str)
            or not isinstance(user.get("user"), dict)
            or not isinstance(user["user"].get("token"), str)
        ):
            raise ValueError("Invalid kubeconfig file format.")


def extract_context_from_kubeconfig(
    kubeconfig: dict, context: Union[str, None] = None
) -> dict:
    """Extracts a context from a kubeconfig file. If the context is not
    specified, the current context is extracted, or if no current context then
    use the first context found. Leave the certficate data in its base64 encoded
    form. Assume that the kubeconfig file is well-formed, does not need
    validation and the context exists. Also assume that it only provides
    certificate authority data and a token for authentication and that it does
    not use a client certificate."""

    # If not context provided see if the current context is specified in the
    # kubeconfig file data, otherwise use the first context found.

    if context is None:
        context = kubeconfig.get("current-context")

        if context is None:
            context = kubeconfig["contexts"][0]["name"]

    # Find the context in the kubeconfig file data.

    context_data = None

    for context_data in kubeconfig["contexts"]:
        if context_data["name"] == context:
            break

    if context_data is None:
        raise ValueError(f"Context {context} not found in kubeconfig file.")

    # Find the cluster and user data for the context.

    cluster_data = None

    for cluster in kubeconfig["clusters"]:
        if cluster["name"] == context_data["context"]["cluster"]:
            cluster_data = cluster
            break

    user_data = None

    for user in kubeconfig["users"]:
        if user["name"] == context_data["context"]["user"]:
            user_data = user
            break

    # Construct a new kubeconfig file with only data releveant to the context.

    kubeconfig = {
        "apiVersion": "v1",
        "kind": "Config",
        "clusters": [cluster_data],
        "contexts": [context_data],
        "current-context": context_data["name"],
        "users": [user_data],
    }

    return kubeconfig


def create_connection_info_from_kubeconfig(config: dict) -> kopf.ConnectionInfo:
    """Create kopf connection info from kubeconfig data."""

    contexts = {}
    clusters = {}
    users = {}

    current_context = None

    if current_context is None:
        current_context = config.get("current-context")

    for item in config.get("contexts", []):
        if item["name"] not in contexts:
            contexts[item["name"]] = item.get("context") or {}

    for item in config.get("clusters", []):
        if item["name"] not in clusters:
            clusters[item["name"]] = item.get("cluster") or {}

    for item in config.get("users", []):
        if item["name"] not in users:
            users[item["name"]] = item.get("user") or {}

    if current_context is None:
        raise ValueError("Current context is not set in kubeconfig.")

    if current_context not in contexts:
        raise ValueError(f"Context {current_context} not found in kubeconfig.")

    context = contexts[current_context]
    cluster = clusters[context["cluster"]]
    user = users[context["user"]]

    provider_token = user.get("auth-provider", {}).get("config", {}).get("access-token")

    return kopf.ConnectionInfo(
        server=cluster.get("server"),
        ca_data=cluster.get("certificate-authority-data"),
        insecure=cluster.get("insecure-skip-tls-verify"),
        certificate_data=user.get("client-certificate-data"),
        private_key_data=user.get("client-key-data"),
        username=user.get("username"),
        password=user.get("password"),
        token=user.get("token") or provider_token,
        default_namespace=context.get("namespace"),
    )
