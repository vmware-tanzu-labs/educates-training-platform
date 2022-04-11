import kopf

from .helpers import global_logger

from .functions_injector import global_configs, reconcile_config

from .config import OPERATOR_API_GROUP


@kopf.on.create(f"secrets.{OPERATOR_API_GROUP}", "v1alpha1", "secretinjectors")
def secretinjector_create(name, body, logger, **_):
    global_configs[name] = body

    with global_logger(logger):
        reconcile_config(name, body)


@kopf.on.resume(f"secrets.{OPERATOR_API_GROUP}", "v1alpha1", "secretinjectors")
def secretinjector_resume(name, body, logger, **_):
    global_configs[name] = body

    with global_logger(logger):
        reconcile_config(name, body)


@kopf.on.update(f"secrets.{OPERATOR_API_GROUP}", "v1alpha1", "secretinjectors")
def secretinjector_update(name, body, logger, **_):
    global_configs[name] = body

    with global_logger(logger):
        reconcile_config(name, body)


@kopf.on.delete(f"secrets.{OPERATOR_API_GROUP}", "v1alpha1", "secretinjectors")
def secretinjector_delete(name, body, **_):
    try:
        del global_configs[name]
    except KeyError:
        pass
