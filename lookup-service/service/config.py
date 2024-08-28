"""Configuration for the lookup service."""

import functools
import random


@functools.lru_cache(maxsize=1)
def jwt_token_secret() -> str:
    """Return the application secret key used to sign the JWT tokens. If we are
    running inside a Kubernetes cluster, we use the in-cluster Kubernetes access
    token as the secret key. Otherwise, we generate a random secret key. The
    result is cached to avoid regenerating the secret key for each request. This
    means that for randomly generated keys, the key will be the same for the
    life of the process. In the case of running in a Kubernetes cluster, the
    secret key will be the same for the life of the container the process runs
    in, with subsequent instances of the container using the same secret key,
    so long as the Kubernetes access token doesn't rotated. When the pod is
    restarted after the Kubernetes access token has rotated, a new secret key
    will be generated and clients will need to login again.
    """

    # Check if we are running inside a Kubernetes cluster and if we are, use the
    # Kubernetes access token as the secret key.

    try:
        with open(
            "/var/run/secrets/kubernetes.io/serviceaccount/token", encoding="utf-8"
        ) as f:
            return f.read()

    except FileNotFoundError:
        # Generate a random secret key using random.choice() to select from a
        # string of characters.

        characters = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
        return "".join(random.choice(characters) for _ in range(64))
