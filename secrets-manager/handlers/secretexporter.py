import kopf

from .helpers import global_logger

from .secretcopier_funcs import reconcile_config

from .operator_config import OPERATOR_API_GROUP


@kopf.index(f"secrets.{OPERATOR_API_GROUP}", "v1beta1", "secretexporters")
def secretexporter_index(namespace, name, body, **_):
    return {(namespace, name): body}


@kopf.on.create(f"secrets.{OPERATOR_API_GROUP}", "v1beta1", "secretexporters")
@kopf.on.resume(f"secrets.{OPERATOR_API_GROUP}", "v1beta1", "secretexporters")
@kopf.on.update(f"secrets.{OPERATOR_API_GROUP}", "v1beta1", "secretexporters")
@kopf.timer(
    f"secrets.{OPERATOR_API_GROUP}", "v1beta1", "secretexporters", interval=60.0
)
def secretexporter_reconcile(name, body, logger, **_):
    with global_logger(logger):
        reconcile_config(name, body)


@kopf.on.delete(
    f"secrets.{OPERATOR_API_GROUP}", "v1beta1", "secretexporters", optional=True
)
def secretexporter_delete(name, body, logger, **_):
    pass
