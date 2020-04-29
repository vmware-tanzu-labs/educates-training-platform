import copy
import json

from aiohttp import web

target_versions = ["v1alpha2"]

api_group = "training.eduk8s.io"


class TranslationError(RuntimeError):
    pass


def convert_Workshop_v1alpha1_to_v1alpha2(resource):
    resource = copy.deepcopy(resource)

    resource["apiVersion"] = f"{api_group}/v1alpha2"

    # Change to structure affecting 'image' and 'content' fields.
    # The 'image' field is no 'content.image'. The 'content' field
    # is now 'content.files'.
    #
    # Version v1alpha1.
    #
    #   image:
    #     type: string
    #   content:
    #     type: string
    #
    # Version v1alpha2.
    #
    #   content:
    #     type: object
    #     properties:
    #       image:
    #         type: string
    #       files:
    #         type: string

    content = resource["spec"].get("content", {})

    if isinstance(content, str):
        content = { "files": content }

    if resource["spec"].get("image") is not None:
        content["image"] = resource["spec"]["image"]
        del resource["spec"]["image"]

    resource["spec"]["content"] = content

    # Change of name from 'workshop' to 'environment'.
    #
    # Version v1alpha1.
    #
    #   workshop:
    #     type: object
    #     properties:
    #       objects:
    #         type: array
    #         items:
    #           type: object
    #           x-kubernetes-preserve-unknown-fields: true
    #
    # Version v1alpha2.
    #
    #   environment:
    #     type: object
    #     properties:
    #       objects:
    #         type: array
    #         items:
    #           type: object
    #           x-kubernetes-preserve-unknown-fields: true

    if resource["spec"].get("environment") is None:
        if resource["spec"].get("workshop") is not None:
            resource["spec"]["environment"] = resource["spec"]["workshop"]
            del resource["spec"]["workshop"]

    return resource


def translate_resource(resource, target):
    resource_kind = resource["kind"]


    target = target.split("/")[-1]

    # We don't currently have conversion being handled by a webhook. Thus we
    # are going to be stored as v1alpha2 even though the resource was created
    # with version v1alpha1. Thus, the 'apiVersion' field actually lies about
    # the version. For now, try and determine the original version from the
    # 'kubectl.kubernetes.io/last-applied-configuration' annotation. If that
    # doesn't exist, presume that we are starting at the oldest version. For
    # now this is safe as conversion routines are not destructive and can be
    # applied on a resource that already appears to have correct fields.

    applied_configuration = resource.get("metadata", {}).get("annotations", {}).get("kubectl.kubernetes.io/last-applied-configuration")

    source = resource["apiVersion"].split("/")[-1]

    if applied_configuration:
        applied_data = json.loads(applied_configuration)
        source = applied_data["apiVersion"].split("/")[-1]
    else:
        source = "v1alpha1"

    while True:
        if source == target:
            return resource

        print(f"Need to convert {resource_kind} from {source} to {target}.")

        for version in target_versions:
            # This is for converting from one version to another.

            convertor_name = f"convert_{resource_kind}_{source}_to_{version}"
            print(f"Lookup translator {convertor_name}.")

            if convertor_name in globals():
                print(f"Translating {resource_kind} from {source} to {version}.")
                convertor_func = globals()[convertor_name]
                resource = convertor_func(resource)
                source = version
                break

        else:
            raise TranslationError(
                f"Unable to translate {resource_kind} to version {target}"
            )


def error_response(version, uid, message):
    return web.json_response(
        {
            "apiVersion": version,
            "kind": "ConversionReview",
            "response": {
                "uid": uid,
                "result": {"status": "Failed", "message": message},
            },
        }
    )


def success_response(version, uid, resources):
    return web.json_response(
        {
            "apiVersion": version,
            "kind": "ConversionReview",
            "response": {
                "uid": uid,
                "result": {"status": "Success"},
                "convertedObjects": resources,
            },
        }
    )


async def translate(request):
    data = await request.json()

    request_version = data["apiVersion"]
    request_kind = data["kind"]

    assert request_version in (
        "apiextensions.k8s.io/v1beta1",
        "apiextensions.k8s.io/v1",
    )
    assert request_kind == "ConversionReview"

    request_uid = data["request"]["uid"]

    desired_version = data["request"]["desiredAPIVersion"]

    processed_resources = []

    for resource in data["request"]["objects"]:
        resource_type = resource["kind"]
        resource_version = resource["apiVersion"]

        group, source_version = resource_version.split("/")

        if group != api_group:
            return error_response(
                request_version,
                request_uid,
                f"Unable to translate resources for API group {group}",
            )

        try:
            processed_resources.append(translate_resource(resource, desired_version))
        except TranslationError as e:
            return error_response(request_version, request_uid, str(e))

    return success_response(request_version, request_uid, processed_resources)


if __name__ == "__main__":
    app = web.Application()
    app.router.add_post("/api/translate", translate)
    web.run_app(app, host="0.0.0.0", port=8080)
