from pykube import object_factory, HTTPClient, KubeConfig
from pykube.objects import APIObject, NamespacedAPIObject

api = HTTPClient(KubeConfig.from_env())


def Resource(api, body):
    return object_factory(api, body["apiVersion"], body["kind"])(api, body)


class Workshop(APIObject):
    version = "training.eduk8s.io/v1alpha2"
    endpoint = "workshops"
    kind = "Workshop"


class WorkshopEnvironment(APIObject):
    version = "training.eduk8s.io/v1alpha1"
    endpoint = "workshopenvironments"
    kind = "WorkshopEnvironment"


class WorkshopSession(APIObject):
    version = "training.eduk8s.io/v1alpha1"
    endpoint = "workshopsessions"
    kind = "WorkshopSession"


class WorkshopRequest(NamespacedAPIObject):
    version = "training.eduk8s.io/v1alpha1"
    endpoint = "workshoprequests"
    kind = "WorkshopRequest"


class WorkshopRequest(APIObject):
    version = "training.eduk8s.io/v1alpha1"
    endpoint = "trainingportals"
    kind = "TrainingPortal"


def create_from_dict(body):
    resource = Resource(api, body)
    resource.create()
