import kubernetes.client

def create_from_dict(body):
    # XXX The Python Kubernetes client doesn't currently support creating
    # custom resources using its create_from_dict() function, so we need
    # to do some hacks for now to get this to work for custom resources.
    # When the client is updated to use the dynamic API internally, then
    # this may eventually work.

    client = kubernetes.client.api_client.ApiClient()
    kubernetes.utils.create_from_dict(client, body)
