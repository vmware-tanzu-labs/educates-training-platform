import os

import kopf

__all__ = ["system_profile_create", "system_profile_resume", "system_profile_update", "system_profile_delete"]


config_name = os.environ.get("SYSTEM_PROFILE", "default-system-profile")

override_ingress_domain = os.environ.get("INGRESS_DOMAIN")
override_ingress_secret = os.environ.get("INGRESS_SECRET")
override_ingress_class = os.environ.get("INGRESS_CLASS")

current_operator_config = None


def operator_ingress_domain():
    if override_ingress_domain:
        return override_ingress_domain

    if current_operator_config is not None:
        domain = current_operator_config.get("ingress", {}).get("domain")
        if domain:
            return domain

    return "training.eduk8s.io"


def operator_ingress_secret():
    if override_ingress_secret:
        return override_ingress_secret

    if current_operator_config is not None:
        secret = current_operator_config.get("ingress", {}).get("secret")
        if secret:
            return secret

    return ""


def operator_ingress_class():
    if override_ingress_class:
        return override_ingress_class

    if current_operator_config is not None:
        klass = current_operator_config.get("ingress", {}).get("class")
        if klass:
            return klass

    return ""


def environment_image_pull_secrets():
    if current_operator_config is not None:
        return (
            current_operator_config.get("environment", {})
            .get("secrets", {})
            .get("pull", [])
        )

    return []


@kopf.on.create("training.eduk8s.io", "v1alpha1", "systemprofiles", id="eduk8s")
def system_profile_create(name, spec, logger, **_):
    if config_name and name == config_name:
        global current_operator_config
        current_operator_config = spec


@kopf.on.resume("training.eduk8s.io", "v1alpha1", "systemprofiles", id="eduk8s")
def system_profile_resume(name, spec, logger, **_):
    if config_name and name == config_name:
        global current_operator_config
        current_operator_config = spec


@kopf.on.update("training.eduk8s.io", "v1alpha1", "systemprofiles", id="eduk8s")
def system_profile_update(name, spec, logger, **_):
    if config_name and name == config_name:
        global current_operator_config
        current_operator_config = spec


@kopf.on.delete(
    "training.eduk8s.io", "v1alpha1", "systemprofiles", id="eduk8s", optional=True
)
def system_profile_delete(name, spec, logger, **_):
    if config_name and name == config_name:
        global current_operator_config
        current_operator_config = None
