import os
import string
import random

import kopf

from config import (
    OPERATOR_API_GROUP,
    RESOURCE_STATUS_KEY,
    IMAGE_REPOSITORY,
)

__all__ = [
    "system_profile_create",
    "system_profile_resume",
    "system_profile_update",
    "system_profile_delete",
]


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
    "BASE_ENVIRONMENT_IMAGE", "$(image_repository)/base-environment:latest"
)
default_jdk8_environment_image = os.environ.get(
    "JDK8_ENVIRONMENT_IMAGE", "$(image_repository)/jdk8-environment:latest"
)
default_jdk11_environment_image = os.environ.get(
    "JDK11_ENVIRONMENT_IMAGE", "$(image_repository)/jdk11-environment:latest"
)
default_conda_environment_image = os.environ.get(
    "CONDA_ENVIRONMENT_IMAGE", "$(image_repository)/conda-environment:latest"
)

default_workshop_images = {
    "base-environment:*": default_base_environment_image,
    "jdk8-environment:*": default_jdk8_environment_image,
    "jdk11-environment:*": default_jdk11_environment_image,
    "conda-environment:*": default_conda_environment_image,
}

default_profile_name = os.environ.get("SYSTEM_PROFILE", "")

default_admin_username = "educates"
default_robot_username = "robot@educates"

default_ingress_domain = os.environ.get(
    "INGRESS_DOMAIN", f"training.{OPERATOR_API_GROUP}"
)
default_ingress_protocol = os.environ.get("INGRESS_PROTOCOL", "http")
default_ingress_secret = os.environ.get("INGRESS_SECRET", "")
default_ingress_class = os.environ.get("INGRESS_CLASS", "")

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


def active_profile_name(profile=None):
    return profile or default_profile_name


def current_profile(profile=None):
    profile = active_profile_name(profile)
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
    return profile_setting(profile, "ingress.domain", default_ingress_domain)


def operator_ingress_protocol(profile=None):
    protocol = profile_setting(profile, "ingress.protocol")

    if not protocol and operator_ingress_secret(profile):
        return "https"

    return protocol or default_ingress_protocol


def operator_ingress_secret(profile=None):
    name = profile_setting(profile, "ingress.secret", default_ingress_secret)

    return name


def operator_ingress_class(profile=None):
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


def registry_image_pull_secret(profile=None):
    return profile_setting(profile, "registry.secret")


def training_portal_image(profile=None):
    image = profile_setting(profile, "portal.image", default_training_portal_image)
    return image.replace("$(image_repository)", IMAGE_REPOSITORY)


def docker_in_docker_image(profile=None):
    image = profile_setting(profile, "dockerd.image", default_docker_in_docker_image)
    return image.replace("$(image_repository)", IMAGE_REPOSITORY)


def docker_registry_image(profile=None):
    image = profile_setting(
        profile, "workshop.registry.image", default_docker_registry_image
    )
    return image.replace("$(image_repository)", IMAGE_REPOSITORY)


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
    return image.replace("$(image_repository)", IMAGE_REPOSITORY)


def analytics_google_tracking_id(profile=None):
    return profile_setting(profile, "analytics.google.trackingId", "")


@kopf.on.create(
    f"training.{OPERATOR_API_GROUP}",
    "v1alpha1",
    "systemprofiles",
    id=RESOURCE_STATUS_KEY,
)
def system_profile_create(name, spec, logger, **_):
    system_profiles[name] = spec


@kopf.on.resume(
    f"training.{OPERATOR_API_GROUP}",
    "v1alpha1",
    "systemprofiles",
    id=RESOURCE_STATUS_KEY,
)
def system_profile_resume(name, spec, logger, **_):
    system_profiles[name] = spec


@kopf.on.update(
    f"training.{OPERATOR_API_GROUP}",
    "v1alpha1",
    "systemprofiles",
    id=RESOURCE_STATUS_KEY,
)
def system_profile_update(name, spec, logger, **_):
    system_profiles[name] = spec


@kopf.on.delete(
    f"training.{OPERATOR_API_GROUP}",
    "v1alpha1",
    "systemprofiles",
    id=RESOURCE_STATUS_KEY,
    optional=True,
)
def system_profile_delete(name, spec, logger, **_):
    try:
        del system_profiles[name]
    except KeyError:
        pass
