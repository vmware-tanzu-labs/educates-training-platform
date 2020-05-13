import os
import string
import random

import kopf

__all__ = [
    "system_profile_create",
    "system_profile_resume",
    "system_profile_update",
    "system_profile_delete",
]


default_portal_image = "quay.io/eduk8s/eduk8s-portal:200509.88f69e8"
default_workshop_image = "quay.io/eduk8s/workshop-dashboard:200512.844177b"

default_profile_name = os.environ.get("SYSTEM_PROFILE", "default-system-profile")

default_admin_username = "eduk8s"
default_robot_username = "robot@eduk8s"

default_ingress_domain = "training.eduk8s.io"
default_ingress_secret = ""
default_ingress_class = ""

override_ingress_domain = os.environ.get("INGRESS_DOMAIN")
override_ingress_secret = os.environ.get("INGRESS_SECRET")
override_ingress_class = os.environ.get("INGRESS_CLASS")

default_storage_class = ""

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
    return profile_setting(
        profile, "portal.credentials.admin.username", default_admin_username
    )


def portal_admin_password(profile=None):
    return profile_setting(
        profile, "portal.credentials.admin.password", generate_password(32)
    )


def portal_robot_username(profile=None):
    return profile_setting(
        profile, "portal.credentials.robot.username", default_robot_username
    )


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


def operator_ingress_secret(profile=None):
    if not profile and override_ingress_secret:
        return override_ingress_secret

    return profile_setting(profile, "ingress.secret", default_ingress_secret)


def operator_ingress_class(profile=None):
    if not profile and override_ingress_class:
        return override_ingress_class

    return profile_setting(profile, "ingress.class", default_ingress_class)


def operator_storage_class(profile=None):
    return profile_setting(profile, "storage.class", default_storage_class)


def portal_container_image(profile=None):
    return profile_setting(profile, "portal.image", default_portal_image)


def environment_image_pull_secrets(profile=None):
    return profile_setting(profile, "environment.secrets.pull", [])


def workshop_container_image(profile=None):
    return profile_setting(profile, "workshop.image", default_workshop_image)


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
