from pykube import object_factory, HTTPClient, KubeConfig
from pykube.objects import APIObject, NamespacedAPIObject

from config import OPERATOR_API_GROUP

api = HTTPClient(KubeConfig.from_env())


def Resource(api, body):
    return object_factory(api, body["apiVersion"], body["kind"])(api, body)


class Workshop(APIObject):
    version = f"training.{OPERATOR_API_GROUP}/v1alpha2"
    endpoint = "workshops"
    kind = "Workshop"


class WorkshopEnvironment(APIObject):
    version = f"training.{OPERATOR_API_GROUP}/v1alpha1"
    endpoint = "workshopenvironments"
    kind = "WorkshopEnvironment"


class WorkshopSession(APIObject):
    version = f"training.{OPERATOR_API_GROUP}/v1alpha1"
    endpoint = "workshopsessions"
    kind = "WorkshopSession"


class WorkshopRequest(NamespacedAPIObject):
    version = f"training.{OPERATOR_API_GROUP}/v1alpha1"
    endpoint = "workshoprequests"
    kind = "WorkshopRequest"


class WorkshopRequest(APIObject):
    version = f"training.{OPERATOR_API_GROUP}/v1alpha1"
    endpoint = "trainingportals"
    kind = "TrainingPortal"


def create_from_dict(body):
    resource = Resource(api, body)
    resource.create()
