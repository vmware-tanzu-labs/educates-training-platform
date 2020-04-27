import copy

from aiohttp import web

target_versions = ["v1alpha2"]

api_group = "training.eduk8s.io"


class TranslationError(RuntimeError):
    pass


def convert_Workshop_v1alpha1_to_v1alpha1(resource):
    resource = copy.deepcopy(resource)

    resource["apiVersion"] = f"{api_group}/v1alpha2"

    # To avoid working out how to convert versions, used 'anyOf' on
    # 'content' to convert it from 'string' to 'object'. The 'content'
    # field becamed 'content.files'. Older way of doing things was:
    #
    #   image:
    #     type: string
    #   content:
    #     type: string
    #
    # New way was:
    #
    #   content:
    #     type: object
    #     properties:
    #       image:
    #         type: string
    #       files:
    #         type: string

    if not isinstance(resource.get("spec", {}).get("content"), dict):
        content = {}

        if resource.get("spec", {}).get("image") is not None:
            content["image"] = resource["spec"]["image"]
            del resource["spec"]["image"]

        if resource.get("spec", {}).get("content") is not None:
            content["files"] = resource["spec"]["content"]
            del resource["spec"]["content"]

        if content:
            resource["spec"]["content"] = content

    # Changed 'workshop' object to 'environment'.

    if resource.get("spec", {}).get("workshop") is not None:
        resource["spec"]["environment"] = resource["spec"]["workshop"]

    return resource


def translate_resource(resource, target):
    resource_kind = resource["kind"]

    source = resource["apiVersion"].split("/")[-1]
    target = target.split("/")[-1]

    while True:
        # This is for performing fixups within same version.

        convertor_name = f"convert_{resource_kind}_{source}_to_{source}"
        print(f"Lookup fixer {convertor_name}.")

        if convertor_name in globals():
            print(f"Fixing {resource_kind} version {source}.")
            convertor_func = globals()[convertor_name]
            resource = convertor_func(resource)

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
