from argparse import Action
from .helpers import xget

from .operator_config import OPERATOR_API_GROUP, OPERATOR_NAME_PREFIX

# Set of rules which are enabled by default.

enabled_rules = []

# A Service of type ExternalName which points back to localhost can potentially
# be used to exploit vulnerabilities in some Ingress controllers. This policy
# audits Services of type ExternalName if the externalName field refers to
# localhost.
#
# https://kyverno.io/policies/other/disallow_localhost_services/disallow_localhost_services/

enabled_rules.append(
    {
        "name": "no-localhost-service",
        "match": {
            "resources": {
                "kinds": ["Service"],
                "namespaceSelector": {
                    "matchExpressions": [
                        {
                            "key": f"training.{OPERATOR_API_GROUP}/environment.name",
                            "operator": "In",
                            "values": ["$(environment_name)"],
                        },
                        {
                            "key": f"training.{OPERATOR_API_GROUP}/component",
                            "operator": "In",
                            "values": ["session"],
                        },
                    ]
                },
            }
        },
        "validate": {
            "message": "Service of type ExternalName cannot point to localhost.",
            "pattern": {
                "spec": {"(type)": "ExternalName", "externalName": "!localhost"}
            },
        },
    },
)

# Set of rules which are disabled by default. None for now.

disabled_rules = []


def kyverno_rules(workshop_spec):
    # First calculate the set of rules to apply. Specific rules can by default
    # enabled or not. What is used can then be overridden by the workshop
    # definition. For now create one cluster policy with all rules in it.

    action = xget(workshop_spec, "session.namespaces.security.rules.action", "enforce")
    overrides = xget(workshop_spec, "session.namespaces.security.rules.overrides", [])

    include = xget(workshop_spec, "session.namespaces.security.rules.include", [])
    exclude = xget(workshop_spec, "session.namespaces.security.rules.exclude", [])

    rules = []

    for rule in enabled_rules:
        if rule["name"] not in exclude:
            rules.append(rule)

    for rule in disabled_rules:
        if rule["name"] in include:
            rules.append(rule)

    if not rules:
        return []

    cluster_policy_body = {
        "apiVersion": "kyverno.io/v1",
        "kind": "ClusterPolicy",
        "metadata": {
            "name": f"{OPERATOR_NAME_PREFIX}-session-$(session_namespace)",
        },
        "spec": {
            "validationFailureAction": action,
            "validationFailureActionOverrides": overrides,
            "background": True,
            "rules": rules,
        },
    }

    return [cluster_policy_body]
