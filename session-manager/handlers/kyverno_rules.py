import os
import yaml
import copy

from .helpers import xget

from .operator_config import OPERATOR_API_GROUP, OPERATOR_NAME_PREFIX

clusterpolicies = []

if os.path.exists("/opt/app-root/config/clusterpolicies.yaml"):
    with open("/opt/app-root/config/clusterpolicies.yaml") as fp:
        clusterpolicies = yaml.load_all(fp.read(), Loader=yaml.Loader)


def kyverno_rules(workshop_spec):
    action = xget(workshop_spec, "session.namespaces.security.rules.action", "enforce")
    exclude = xget(workshop_spec, "session.namespaces.security.rules.exclude", [])

    rules = []

    for clusterpolicy in clusterpolicies:
        policy_name = xget(clusterpolicy, "metadata.name")
        policy_rules = xget(clusterpolicy, "spec.rules", [])

        for index, rule in enumerate(policy_rules, start=1):
            rule = copy.deepcopy(rule)

            if len(policy_rules) != 1:
                rule["name"] = f"{policy_name}/{index}"
            else:
                rule["name"] = policy_name

            resources = xget(rule, "match.all", [])

            if not resources:
                resources = xget(rule, "match.any", [])

            if not resources:
                resources = [xget(rule, "match.resources", {})]

            if not resources:
                continue

            for resource in resources:
                resource["namespaceSelector"] = {
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
                }

            if policy_name not in exclude:
                rules.append(rule)

    if not rules:
        return []

    cluster_policy_body = {
        "apiVersion": "kyverno.io/v1",
        "kind": "ClusterPolicy",
        "metadata": {
            "name": f"{OPERATOR_NAME_PREFIX}-environment-$(environment_name)",
        },
        "spec": {
            "validationFailureAction": action,
            "background": True,
            "rules": rules,
        },
    }

    return [cluster_policy_body]
