import kopf

from .helpers import global_logger

from .secretcopier_funcs import reconcile_config

from .config import OPERATOR_API_GROUP


@kopf.index(f"secrets.{OPERATOR_API_GROUP}", "v1alpha1", "secretcopiers")
def secretcopier_index(name, body, **_):
    return {(None, name): body}


@kopf.on.create(f"secrets.{OPERATOR_API_GROUP}", "v1alpha1", "secretcopiers")
@kopf.on.resume(f"secrets.{OPERATOR_API_GROUP}", "v1alpha1", "secretcopiers")
@kopf.on.update(f"secrets.{OPERATOR_API_GROUP}", "v1alpha1", "secretcopiers")
@kopf.timer(f"secrets.{OPERATOR_API_GROUP}", "v1alpha1", "secretcopiers", interval=60.0)
def secretcopier_reconcile(name, body, logger, **_):
    with global_logger(logger):
        reconcile_config(name, body)
