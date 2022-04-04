import os
import string
import random

import kopf

from config import OPERATOR_NAMESPACE

__all__ = [
    "system_profile_create",
    "system_profile_resume",
    "system_profile_update",
    "system_profile_delete",
]


default_image_repository = os.environ.get(
    "IMAGE_REPOSITORY", f"registry.{OPERATOR_NAMESPACE}.svc.cluster.local:5001"
)

default_training_portal_image = os.environ.get(
    "TRAINING_PORTAL_IMAGE", "$(image_repository)/educates-training-portal:latest"
)
default_docker_in_docker_image = os.environ.get(
    "DOCKER_IN_DOCKER_IMAGE", "$(image_repository)/educates-docker-in-docker:latest"
)
default_docker_registry_image = os.environ.get(
    "DOCKER_REGISTRY_IMAGE", "$(image_repository)/educates-docker-registry:latest"
)
default_base_environment_image = os.environ.get(
    "BASE_ENVIRONMENT_IMAGE", "base-environment:latest"
)
default_jdk8_environment_image = os.environ.get(
    "JDK8_ENVIRONMENT_IMAGE", "jdk8-environment:latest"
)
default_jdk11_environment_image = os.environ.get(
    "JDK11_ENVIRONMENT_IMAGE", "jdk11-environment:latest"
)
default_conda_environment_image = os.environ.get(
    "CONDA_ENVIRONMENT_IMAGE", "conda-environment:latest"
)


default_workshop_images = {
    "base-environment:*": default_base_environment_image,
    "base-environment:develop": "$(image_repository)/educates-base-environment:develop",
    "base-environment:latest": "$(image_repository)/educates-base-environment:latest",
    "base-environment:master": "$(image_repository)/educates-base-environment:master",
    "jdk8-environment:*": default_jdk8_environment_image,
    "jdk8-environment:develop": "$(image_repository)/educates-jdk8-environment:develop",
    "jdk8-environment:latest": "$(image_repository)/educates-jdk8-environment:latest",
    "jdk8-environment:master": "$(image_repository)/educates-jdk8-environment:master",
    "jdk11-environment:*": default_jdk11_environment_image,
    "jdk11-environment:develop": "$(image_repository)/jeducates-dk11-environment:develop",
    "jdk11-environment:latest": "$(image_repository)/educates-jdk11-environment:latest",
    "jdk11-environment:master": "$(image_repository)/educates-jdk11-environment:master",
    "conda-environment:*": default_conda_environment_image,
    "conda-environment:develop": "$(image_repository)/educates-conda-environment:develop",
    "conda-environment:latest": "$(image_repository)/educates-conda-environment:latest",
    "conda-environment:master": "$(image_repository)/educates-conda-environment:master",
}

default_profile_name = os.environ.get("SYSTEM_PROFILE", "default-system-profile")

default_admin_username = "educates"
default_robot_username = "robot@educates"

default_ingress_domain = "training.eduk8s.io"
default_ingress_protocol = "http"
default_ingress_secret = ""
default_ingress_class = ""

override_ingress_domain = os.environ.get("INGRESS_DOMAIN")
override_ingress_protocol = os.environ.get("INGRESS_PROTOCOL")
override_ingress_secret = os.environ.get("INGRESS_SECRET")
override_ingress_class = os.environ.get("INGRESS_CLASS")

if override_ingress_secret and not "/" in override_ingress_secret:
    override_ingress_secret = f"{OPERATOR_NAMESPACE}/{override_ingress_secret}"

default_storage_class = ""
default_storage_user = None
default_storage_group = 0

default_dockerd_mtu = 1400
default_dockerd_mirror_remote = None
default_dockerd_mirror_username = ""
default_dockerd_mirror_password = ""
default_dockerd_rootless = True
default_dockerd_privileged = True

default_network_blockcidrs = []

system_profiles = {}


def current_profile(profile=None):
    profile = profile or default_profile_name
    return system_profiles.get(profile)


def profile_setting(profile, key, default=None):
    properties = current_profile(profile) or {}

    keys = key.split(".")
    value = default

    for key in keys:
        value = properties.get(key)
        if value is None:
            return default

        properties = value

    return value


def generate_password(length):
    characters = string.ascii_letters + string.digits
    return "".join(random.sample(characters, length))


def portal_admin_username(profile=None):
    value = profile_setting(profile, "portal.credentials.admin.username")
    return value or default_admin_username


def portal_admin_password(profile=None):
    return profile_setting(
        profile, "portal.credentials.admin.password", generate_password(32)
    )


def portal_robot_username(profile=None):
    value = profile_setting(profile, "portal.credentials.robot.username")
    return value or default_robot_username


def portal_robot_password(profile=None):
    return profile_setting(
        profile, "portal.credentials.robot.password", generate_password(32)
    )


def portal_robot_client_id(profile=None):
    return profile_setting(profile, "portal.clients.robot.id", generate_password(32))


def portal_robot_client_secret(profile=None):
    return profile_setting(
        profile, "portal.clients.robot.secret", generate_password(32)
    )


def operator_ingress_domain(profile=None):
    if not profile and override_ingress_domain:
        return override_ingress_domain

    return profile_setting(profile, "ingress.domain", default_ingress_domain)


def operator_ingress_protocol(profile=None):
    if not profile and override_ingress_protocol:
        return override_ingress_protocol

    protocol = profile_setting(profile, "ingress.protocol")

    if not protocol and operator_ingress_secret(profile):
        return "https"

    return protocol or default_ingress_protocol


def operator_ingress_secret(profile=None):
    if not profile and override_ingress_secret:
        return override_ingress_secret

    name = profile_setting(profile, "ingress.secret", default_ingress_secret)

    if name and not "/" in name:
        name = f"{OPERATOR_NAMESPACE}/{name}"

    return name


def operator_ingress_class(profile=None):
    if not profile and override_ingress_class:
        return override_ingress_class

    return profile_setting(profile, "ingress.class", default_ingress_class)


def operator_storage_class(profile=None):
    return profile_setting(profile, "storage.class", default_storage_class)


def operator_storage_user(profile=None):
    return profile_setting(profile, "storage.user", default_storage_user)


def operator_storage_group(profile=None):
    return profile_setting(profile, "storage.group", default_storage_group)


def operator_dockerd_mtu(profile=None):
    return profile_setting(profile, "dockerd.mtu", default_dockerd_mtu)


def operator_dockerd_mirror_remote(profile=None):
    return profile_setting(
        profile, "dockerd.mirror.remote", default_dockerd_mirror_remote
    )


def operator_dockerd_mirror_username(profile=None):
    return profile_setting(
        profile, "dockerd.mirror.username", default_dockerd_mirror_username
    )


def operator_dockerd_mirror_password(profile=None):
    return profile_setting(
        profile, "dockerd.mirror.password", default_dockerd_mirror_password
    )


def operator_dockerd_rootless(profile=None):
    return profile_setting(profile, "dockerd.rootless", default_dockerd_rootless)


def operator_dockerd_privileged(profile=None):
    return profile_setting(profile, "dockerd.privileged", default_dockerd_privileged)


def operator_network_blockcidrs(profile=None):
    return profile_setting(profile, "network.blockCIDRs", default_network_blockcidrs)


def image_repository(profile=None):
    host = profile_setting(profile, "registry.host")

    if not host:
        return default_image_repository

    namespace = profile_setting(profile, "registry.namespace")

    return namespace and "/".join([host, namespace]) or host


def registry_image_pull_secret(profile=None):
    return profile_setting(profile, "registry.secret")


def training_portal_image(profile=None):
    image = profile_setting(profile, "portal.image", default_training_portal_image)
    return image.replace("$(image_repository)", image_repository(profile))


def docker_in_docker_image(profile=None):
    image = profile_setting(profile, "dockerd.image", default_docker_in_docker_image)
    return image.replace("$(image_repository)", image_repository(profile))


def docker_registry_image(profile=None):
    image = profile_setting(
        profile, "workshop.registry.image", default_docker_registry_image
    )
    return image.replace("$(image_repository)", image_repository(profile))


def environment_image_pull_secrets(profile=None):
    return profile_setting(profile, "environment.secrets.pull", [])


def theme_dashboard_script(profile=None):
    return profile_setting(profile, "theme.dashboard.script", "")


def theme_dashboard_style(profile=None):
    return profile_setting(profile, "theme.dashboard.style", "")


def theme_workshop_script(profile=None):
    return profile_setting(profile, "theme.workshop.script", "")


def theme_workshop_style(profile=None):
    return profile_setting(profile, "theme.workshop.style", "")


def theme_portal_script(profile=None):
    return profile_setting(profile, "theme.portal.script", "")


def theme_portal_style(profile=None):
    return profile_setting(profile, "theme.portal.style", "")


def workshop_container_image(image, profile=None):
    image = image or "base-environment:*"
    image = profile_setting(profile, "workshop.images", {}).get(image, image)
    image = default_workshop_images.get(image, image)
    return image.replace("$(image_repository)", image_repository(profile))


def analytics_google_tracking_id(image, profile=None):
    return profile_setting(profile, "analytics.google.trackingId", "")


@kopf.on.create("training.eduk8s.io", "v1alpha1", "systemprofiles", id="eduk8s")
def system_profile_create(name, spec, logger, **_):
    system_profiles[name] = spec


@kopf.on.resume("training.eduk8s.io", "v1alpha1", "systemprofiles", id="eduk8s")
def system_profile_resume(name, spec, logger, **_):
    system_profiles[name] = spec


@kopf.on.update("training.eduk8s.io", "v1alpha1", "systemprofiles", id="eduk8s")
def system_profile_update(name, spec, logger, **_):
    system_profiles[name] = spec


@kopf.on.delete(
    "training.eduk8s.io", "v1alpha1", "systemprofiles", id="eduk8s", optional=True
)
def system_profile_delete(name, spec, logger, **_):
    try:
        del system_profiles[name]
    except KeyError:
        pass
