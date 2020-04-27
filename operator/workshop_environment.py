import os
import yaml

import kopf
import kubernetes
import kubernetes.client
import kubernetes.utils

from objects import create_from_dict
from translator import translate_resource

__all__ = ["workshop_environment_create", "workshop_environment_delete"]


@kopf.on.create("training.eduk8s.io", "v1alpha1", "workshopenvironments", id="eduk8s")
def workshop_environment_create(name, spec, logger, **_):
    core_api = kubernetes.client.CoreV1Api()
    custom_objects_api = kubernetes.client.CustomObjectsApi()
    rbac_authorization_api = kubernetes.client.RbacAuthorizationV1Api()

    # Use the name of the custom resource as the name of the namespace
    # under which the workshop environment is created and any workshop
    # instances are created.

    environment_name = name
    workshop_namespace = environment_name

    # The name of the workshop to be deployed can differ and is taken
    # from the specification of the workspace. Lookup the workshop
    # resource definition and ensure it exists. Later we will stash a
    # copy of this in the status of the custom resource, and we will use
    # this copy to avoid being affected by changes in the original after
    # the creation of the workshop environment.

    workshop_name = spec["workshop"]["name"]

    try:
        workshop_instance = custom_objects_api.get_cluster_custom_object(
            "training.eduk8s.io", "v1alpha1", "workshops", workshop_name
        )
    except kubernetes.client.rest.ApiException as e:
        if e.status == 404:
            raise kopf.TemporaryError(f"Workshop {workshop_name} is not available.")

    workshop_instance = translate_resource(workshop_instance, "v1alpha1")

    workshop_spec = workshop_instance.get("spec", {})

    # Calculate which additional applications are enabled for a workshop
    # and provide some helper functions to work with their configuration.

    applications = {}

    if workshop_spec.get("session"):
        applications = workshop_spec["session"].get("applications", {})

    application_defaults = {
        "docker": False,
        "editor": False,
        "console": False,
        "registry": False,
        "slides": True,
        "terminal": True,
    }

    def is_application_enabled(name):
        return applications.get(name, {}).get(
            "enabled", application_defaults.get(name, False)
        )

    def application_property(name, key, default=None):
        properties = applications.get(name, {})
        keys = key.split(".")
        value = default
        for key in keys:
            value = properties.get(key)
            if value is None:
                return default
            properties = value
        return value

    # Create the namespace for everything related to this workshop.

    namespace_body = {
        "apiVersion": "v1",
        "kind": "Namespace",
        "metadata": {"name": workshop_namespace},
    }

    # Make the namespace for the workshop a child of the custom resource
    # for the workshop environment. This way the namespace will be
    # automatically deleted when the resource definition for the
    # workshop environment is deleted and we don't have to clean up
    # anything explicitly.

    kopf.adopt(namespace_body)

    namespace_instance = core_api.create_namespace(body=namespace_body)

    # Make a copy of the TLS secret into the workshop namespace.

    ingress_protocol = "http"

    default_domain = os.environ.get("INGRESS_DOMAIN", "training.eduk8s.io")
    default_secret = os.environ.get("INGRESS_SECRET", "")

    ingress_domain = (
        spec.get("session", {}).get("ingress", {}).get("domain", default_domain)
    )

    if ingress_domain == default_domain:
        ingress_secret = default_secret
    else:
        ingress_secret = spec.get("session", {}).get("ingress", {}).get("secret", "")

    if ingress_secret:
        try:
            ingress_secret_instance = core_api.read_namespaced_secret(
                namespace="eduk8s", name=ingress_secret
            )
        except kubernetes.client.rest.ApiException as e:
            if e.status == 404:
                raise kopf.TemporaryError(
                    f"TLS secret {ingress_secret} is not available."
                )
            raise

        if not ingress_secret_instance.data.get(
            "tls.crt"
        ) or not ingress_secret_instance.data.get("tls.key"):
            raise kopf.TemporaryError(f"TLS secret {ingress_secret} is not valid.")

        ingress_protocol = "https"

        secret_body = {
            "apiVersion": "v1",
            "kind": "Secret",
            "metadata": {"name": ingress_secret},
            "type": "kubernetes.io/tls",
            "data": {
                "tls.crt": ingress_secret_instance.data["tls.crt"],
                "tls.key": ingress_secret_instance.data["tls.key"],
            },
        }

        core_api.create_namespaced_secret(
            namespace=workshop_namespace, body=secret_body
        )

    # Delete any limit ranges applied to the namespace so they don't
    # cause issues with workshop instance deployments or any workshop
    # deployments.

    limit_ranges = core_api.list_namespaced_limit_range(namespace=workshop_namespace)

    for limit_range in limit_ranges.items:
        core_api.delete_namespaced_limit_range(
            namespace=workshop_namespace, name=limit_range["metadata"]["name"]
        )

    # Delete any resource quotas applied to the namespace so they don't
    # cause issues with workshop instance deploymemnts or any workshop
    # resources.

    resource_quotas = core_api.list_namespaced_resource_quota(
        namespace=workshop_namespace
    )

    for resource_quota in resource_quotas.items:
        core_api.delete_namespaced_resource_quota(
            namespace=workshop_namespace, name=resource_quota["metadata"]["name"]
        )

    # Create a config map in the workshop namespace which contains the
    # details about the workshop. This will be mounted into workshop
    # instances so they can derived information to configure themselves.

    workshop_data = yaml.dump(workshop_instance, Dumper=yaml.Dumper)

    config_map_body = {
        "apiVersion": "v1",
        "kind": "ConfigMap",
        "metadata": {"name": f"workshop"},
        "data": {"workshop.yaml": workshop_data},
    }

    kopf.adopt(config_map_body)

    core_api.create_namespaced_config_map(
        namespace=workshop_namespace, body=config_map_body
    )

    # Because the Kubernetes web console is designed for working against
    # a whole cluster and we want to use it in scope of a single
    # namespace, we need to at least grant it roles to be able to list
    # and get namespaces. If we don't do this then the web console will
    # forever generate a stream of events complaining that it can't read
    # namespaces. This seems to hasten the web console hanging, but also
    # means can't easily switch to other namespaces the workshop has
    # access to as the list of namespaces cannot be generated. At this
    # point we therefore create a cluster role associated with the
    # name of the namespace create for the workshop environment. This
    # will later be bound to the service account the workshop
    # instances and web consoles runs as. As with the namespace we add
    # it as a child to the custom resource for the workshop.

    cluster_role_body = {
        "apiVersion": "rbac.authorization.k8s.io/v1",
        "kind": "ClusterRole",
        "metadata": {"name": f"{workshop_namespace}-console"},
        "rules": [
            {"apiGroups": [""], "resources": ["namespaces"], "verbs": ["get", "list"]}
        ],
    }

    kopf.adopt(cluster_role_body)

    cluster_role_instance = rbac_authorization_api.create_cluster_role(
        body=cluster_role_body
    )

    # Create any additional resources required for the workshop, as
    # defined by the workshop resource definition and extras from the
    # workshop environment itself. Where a namespace isn't defined for a
    # namespaced resource type, the resource will be created in the
    # workshop namespace.
    #
    # XXX For now make the workshop environment resource definition the
    # parent of all objects. Technically should only do so for non
    # namespaced objects, or objects created in namespaces that already
    # existed. How to work out if a resource type is namespaced or not
    # with the Python Kubernetes client appears to be a bit of a hack.

    environment_token = spec.get("request", {}).get("token", "")

    def _substitute_variables(obj):
        if isinstance(obj, str):
            obj = obj.replace("$(workshop_name)", workshop_name)
            obj = obj.replace("$(environment_name)", environment_name)
            obj = obj.replace("$(environment_token)", environment_token)
            obj = obj.replace("$(workshop_namespace)", workshop_namespace)
            obj = obj.replace("$(ingress_domain)", ingress_domain)
            obj = obj.replace("$(ingress_protocol)", ingress_protocol)
            obj = obj.replace("$(ingress_secret)", ingress_secret)
            return obj
        elif isinstance(obj, dict):
            return {k: _substitute_variables(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [_substitute_variables(v) for v in obj]
        else:
            return obj

    if workshop_instance["spec"].get("workshop", {}).get("objects"):
        objects = workshop_instance["spec"]["workshop"]["objects"]

        for object_body in objects:
            object_body = _substitute_variables(object_body)

            if not object_body["metadata"].get("namespace"):
                object_body["metadata"]["namespace"] = workshop_namespace

            kopf.adopt(object_body)

            create_from_dict(object_body)

    if spec.get("environment", {}).get("objects"):
        objects = spec["environment"]["objects"]

        for object_body in objects:
            object_body = _substitute_variables(object_body)

            if not object_body["metadata"].get("namespace"):
                object_body["metadata"]["namespace"] = workshop_namespace

            kopf.adopt(object_body)

            create_from_dict(object_body)

    # Create workshop objects for docker application.

    if is_application_enabled("docker"):
        docker_objects = [
            {
                "apiVersion": "policy/v1beta1",
                "kind": "PodSecurityPolicy",
                "metadata": {"name": "$(workshop_namespace)-docker"},
                "spec": {
                    "privileged": True,
                    "allowPrivilegeEscalation": True,
                    "requiredDropCapabilities": ["KILL", "MKNOD", "SETUID", "SETGID"],
                    "hostIPC": False,
                    "hostNetwork": False,
                    "hostPID": False,
                    "hostPorts": [],
                    "runAsUser": {"rule": "RunAsAny"},
                    "seLinux": {"rule": "RunAsAny"},
                    "fsGroup": {"rule": "RunAsAny"},
                    "supplementalGroups": {"rule": "RunAsAny"},
                    "volumes": [
                        "configMap",
                        "downwardAPI",
                        "emptyDir",
                        "persistentVolumeClaim",
                        "projected",
                        "secret",
                    ],
                },
            },
            {
                "apiVersion": "rbac.authorization.k8s.io/v1",
                "kind": "ClusterRole",
                "metadata": {"name": "$(workshop_namespace)-docker"},
                "rules": [
                    {
                        "apiGroups": ["policy"],
                        "resources": ["podsecuritypolicies"],
                        "verbs": ["use"],
                        "resourceNames": ["$(workshop_namespace)-docker"],
                    }
                ],
            },
        ]

        for object_body in docker_objects:
            object_body = _substitute_variables(object_body)
            kopf.adopt(object_body)
            create_from_dict(object_body)

    # Save away the specification of the workshop in the status for the
    # custom resourcse. We will use this later when creating any
    # workshop instances so always working with the same version.

    return {
        "namespace": workshop_namespace,
        "workshop": {"name": workshop_name, "spec": workshop_instance["spec"],},
    }


@kopf.on.delete("training.eduk8s.io", "v1alpha1", "workshopenvironments", optional=True)
def workshop_environment_delete(name, spec, logger, **_):
    # Nothing to do here at this point because the owner references will
    # ensure that everything is cleaned up appropriately.

    pass
