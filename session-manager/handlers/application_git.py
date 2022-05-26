import random
import string

from .operator_config import OPERATOR_API_GROUP, INGRESS_DOMAIN, INGRESS_PROTOCOL


def git_workshop_spec_patches(workshop_spec, application_properties):
    characters = string.ascii_letters + string.digits

    git_host = f"git-$(session_namespace).{INGRESS_DOMAIN}"
    git_username = "$(session_namespace)"
    git_password = "".join(random.sample(characters, 32))

    return {
        "spec": {
            "session": {
                "ingresses": [
                    {"name": "git", "port": 10087, "authentication": {"type": "none"}}
                ],
                "variables": [
                    {
                        "name": "git_protocol",
                        "value": INGRESS_PROTOCOL,
                    },
                    {
                        "name": "git_host",
                        "value": git_host,
                    },
                    {
                        "name": "git_username",
                        "value": git_username,
                    },
                    {
                        "name": "git_password",
                        "value": git_password,
                    },
                ],
                "env": [
                    {
                        "name": "GIT_PROTOCOL",
                        "value": INGRESS_PROTOCOL,
                    },
                    {
                        "name": "GIT_HOST",
                        "value": git_host,
                    },
                    {
                        "name": "GIT_USERNAME",
                        "value": git_username,
                    },
                    {
                        "name": "GIT_PASSWORD",
                        "value": git_password,
                    },
                ],
            }
        }
    }


def git_environment_objects_list(workshop_spec, application_properties):
    return []


def git_session_objects_list(workshop_spec, application_properties):
    return []


def git_pod_template_spec_patches(workshop_spec, application_properties):
    return {}
