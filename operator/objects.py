import pykube

api = pykube.HTTPClient(pykube.KubeConfig.from_env())


def create_from_dict(body):
    kind = body["kind"]
    api_version = body["apiVersion"]

    pykube.object_factory(api, api_version, kind)(api, body).create()
