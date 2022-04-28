from .application_git import (
    git_workshop_spec_patches,
    git_environment_objects_list,
    git_session_objects_list,
    git_pod_template_spec_patches,
)
from .application_vcluster import (
    vcluster_workshop_spec_patches,
    vcluster_environment_objects_list,
    vcluster_session_objects_list,
    vcluster_pod_template_spec_patches,
)


registered_applications = {
    "git": dict(
        workshop_spec_patches=git_workshop_spec_patches,
        environment_objects_list=git_environment_objects_list,
        session_objects_list=git_session_objects_list,
        pod_template_spec_patches=git_pod_template_spec_patches,
    ),
    "vcluster": dict(
        workshop_spec_patches=vcluster_workshop_spec_patches,
        environment_objects_list=vcluster_environment_objects_list,
        session_objects_list=vcluster_session_objects_list,
        pod_template_spec_patches=vcluster_pod_template_spec_patches,

    ),
}


def workshop_spec_patches(application, application_properties):
    handler = registered_applications.get(application, {}).get(
        "workshop_spec_patches"
    )
    if handler:
        return handler(application_properties)
    return {}


def environment_objects_list(application, application_properties):
    handler = registered_applications.get(application, {}).get(
        "environment_objects_list"
    )
    if handler:
        return handler(application_properties)
    return []


def session_objects_list(application, application_properties):
    handler = registered_applications.get(application, {}).get("session_objects_list")
    if handler:
        return handler(application_properties)
    return []


def pod_template_spec_patches(application, application_properties):
    handler = registered_applications.get(application, {}).get(
        "pod_template_spec_patches"
    )
    if handler:
        return handler(application_properties)
    return {}



