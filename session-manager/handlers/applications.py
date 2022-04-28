from .application_vcluster import (
    vcluster_environment_objects_list,
    vcluster_session_objects_list,
    vcluster_pod_template_spec_patches,
    vcluster_workshop_config_patches,
)


registered_applications = {
    "vcluster": dict(
        environment_objects_list=vcluster_environment_objects_list,
        session_objects_list=vcluster_session_objects_list,
        pod_template_spec_patches=vcluster_pod_template_spec_patches,
        workshop_config_patches=vcluster_workshop_config_patches,
    )
}


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


def workshop_config_patches(application, application_properties):
    handler = registered_applications.get(application, {}).get("workshop_config_patches")
    if handler:
        return handler(application_properties)
    return {}
