import os

import kopf

__all__ = [
    "system_profile_create",
    "system_profile_resume",
    "system_profile_update",
    "system_profile_delete",
]


default_profile_name = os.environ.get("SYSTEM_PROFILE", "default-system-profile")

override_ingress_domain = os.environ.get("INGRESS_DOMAIN")
override_ingress_secret = os.environ.get("INGRESS_SECRET")
override_ingress_class = os.environ.get("INGRESS_CLASS")

system_profiles = {}


def current_profile(profile=None):
    profile = profile or default_profile_name
    return system_profiles.get(profile)


def operator_ingress_domain(profile=None):
    if not profile and override_ingress_domain:
        return override_ingress_domain

    selected_profile = current_profile(profile)

    if selected_profile is not None:
        domain = selected_profile.get("ingress", {}).get("domain")
        if domain:
            return domain

    return "training.eduk8s.io"


def operator_ingress_secret(profile=None):
    if not profile and override_ingress_secret:
        return override_ingress_secret

    selected_profile = current_profile(profile)

    if selected_profile is not None:
        secret = selected_profile.get("ingress", {}).get("secret")
        if secret:
            return secret

    return ""


def operator_ingress_class(profile=None):
    if not profile and override_ingress_class:
        return override_ingress_class

    selected_profile = current_profile(profile)

    if selected_profile is not None:
        klass = selected_profile.get("ingress", {}).get("class")
        if klass:
            return klass

    return ""


def operator_storage_class(profile=None):
    selected_profile = current_profile(profile)

    if selected_profile is not None:
        klass = selected_profile.get("storage", {}).get("class")
        if klass:
            return klass

    return ""


def environment_image_pull_secrets(profile=None):
    selected_profile = current_profile(profile)

    if selected_profile is not None:
        return (
            selected_profile.get("environment", {}).get("secrets", {}).get("pull", [])
        )

    return []


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
