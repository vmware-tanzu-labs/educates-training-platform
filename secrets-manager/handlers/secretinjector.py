import kopf

from .helpers import global_logger

from .secretinjector_funcs import reconcile_config

from .config import OPERATOR_API_GROUP


@kopf.index(f"secrets.{OPERATOR_API_GROUP}", "v1alpha1", "secretinjectors")
def secretinjector_index(name, body, **_):
    return {(None, name): body}


@kopf.on.create(f"secrets.{OPERATOR_API_GROUP}", "v1alpha1", "secretinjectors")
@kopf.on.resume(f"secrets.{OPERATOR_API_GROUP}", "v1alpha1", "secretinjectors")
@kopf.on.update(f"secrets.{OPERATOR_API_GROUP}", "v1alpha1", "secretinjectors")
def secretinjector_update(name, body, logger, **_):
    with global_logger(logger):
        reconcile_config(name, body)
