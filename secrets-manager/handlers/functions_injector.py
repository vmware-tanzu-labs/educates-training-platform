import fnmatch

import pykube

from .helpers import get_logger, lookup

global_configs = {}


def matches_target_namespace(namespace_name, namespace_obj, configs=None):
    """Returns all rules which match the namespace passed as argument."""

    if configs is None:
        configs = global_configs.values()

    for config_obj in configs:
        rules = lookup(config_obj, "spec.rules", [])

        for rule in rules:
            # Note that as soon as one selector fails where a condition
            # was stipulated, further checks are not done and the
            # namespace is ignored. In other words all conditions much
            # match if more than one is supplied.

            # Check for where name selector is provided and ensure that
            # the namespace is in the list, or is not excluded by a
            # negated entry. If a list is supplied but it isn't in the
            # list, or is prohibited by negation, then we skip to the
            # next one. If not list is supplied a default list of
            # negated entries is used which blocks Kubernetes system
            # namespaces. Matching of names allows for glob wildcards.

            match_names = lookup(rule, "targetNamespaces.nameSelector.matchNames")

            if match_names is None:
                match_names = ["!kube-*"]

            match_exclude_names = list(
                map(lambda _: _[1:], filter(lambda _: _.startswith("!"), match_names))
            )
            match_include_names = list(
                filter(lambda _: not _.startswith("!"), match_names)
            )

            def glob_match_name(name, items):
                for item in items:
                    if fnmatch.fnmatch(name, item):
                        return True
                return False

            if match_include_names and not glob_match_name(
                namespace_name, match_include_names
            ):
                continue

            if match_exclude_names and glob_match_name(
                namespace_name, match_exclude_names
            ):
                continue

            # Check if object uid selector is provided and ensure that
            # uid of the target namespace is in the list. If a list is
            # supplied but it isn't in the list, then skip to the next
            # one.

            match_uids = lookup(rule, "targetNamespaces.uidSelector.matchUIDs", [])

            if match_uids:
                namespace_uid = lookup(namespace_obj, "metadata.uid", "")
                if namespace_uid not in match_uids:
                    continue

            # Check for where label selector is provided and ensure that
            # all the labels to be matched exist on the target namespace.

            match_labels = lookup(
                rule, "targetNamespaces.labelSelector.matchLabels", {}
            )

            if match_labels:
                matches = True
                namespace_labels = lookup(namespace_obj, "metadata.labels", {})
                for key, value in match_labels.items():
                    if namespace_labels.get(key) != value:
                        matches = False
                        break
                if not matches:
                    continue

            # Check for where label selector is provided but with more
            # general match expressions. Ensure that all the expressions
            # match the labels on the target namespace.

            match_expressions = lookup(
                rule, "targetNamespaces.labelSelector.matchExpressions", []
            )

            if match_expressions:
                matches = True
                namespace_labels = lookup(namespace_obj, "metadata.labels", {})
                for item in match_expressions:
                    key = item["key"]
                    operator = item["operator"]
                    values = item.get("values", [])
                    value = namespace_labels.get(key)
                    if operator == "In":
                        if values:
                            if value is None or value not in values:
                                matches = False
                                break
                    elif operator == "NotIn":
                        if values:
                            if value is not None and value in values:
                                matches = False
                                break
                    elif operator == "Exists":
                        if key not in namespace_labels:
                            matches = False
                            break
                    elif operator == "DoesNotExist":
                        if key in namespace_labels:
                            matches = False
                            break
                if not matches:
                    continue

            yield rule


def matches_source_secret(secret_name, secret_obj, rule):
    """Returns true if the rule matches against the name of the specified
    secret.

    """

    # Note that as soon as one selector fails where a condition was
    # stipulated, further checks are not done and the secret is ignored.
    # In other words all conditions much match if more than one is
    # supplied.

    # Check for where name selector is provided and ensure that
    # the secret is in the list. If a list is supplied but it
    # isn't in the list, then we skip to the next one. If both a
    # name selector and label selector exist, the label selector
    # will be ignored.

    match_names = lookup(rule, "sourceSecrets.nameSelector.matchNames", [])

    if match_names:
        if secret_name not in match_names:
            return False

    # Check for were label selector is provided and ensure that
    # all the labels to be matched exist on the target namespace.

    match_labels = lookup(rule, "sourceSecrets.labelSelector.matchLabels", {})

    if match_labels:
        labels = lookup(secret_obj, "metadata.labels", {})
        for key, value in match_labels.items():
            if labels.get(key) != value:
                return False

    # Check for where label selector is provided but with more
    # general match expressions. Ensure that all the expressions
    # match the labels on the target secret.

    match_expressions = lookup(rule, "sourceSecrets.labelSelector.matchExpressions", [])

    if match_expressions:
        secret_labels = lookup(secret_obj, "metadata.labels", {})
        for item in match_expressions:
            key = item["key"]
            operator = item["operator"]
            values = item.get("values", [])
            value = secret_labels.get(key)
            if operator == "In":
                if values:
                    if value is None or value not in values:
                        return False
            elif operator == "NotIn":
                if values:
                    if value is not None and value in values:
                        return False
            elif operator == "Exists":
                if key not in secret_labels:
                    return False
            elif operator == "DoesNotExist":
                if key in secret_labels:
                    return False

    return True


def matches_service_account(service_account_name, service_account_obj, rule):
    """Returns true if the rule matches against the name of the specified
    service account.

    """

    # Note that as soon as one selector fails where a condition was
    # stipulated, further checks are not done and the secret is ignored.
    # In other words all conditions much match if more than one is
    # supplied.

    # Check for where name selector is provided and ensure that
    # the secret is in the list. If a list is supplied but it
    # isn't in the list, then we skip to the next one. If both a
    # name selector and label selector exist, the label selector
    # will be ignored.

    match_names = lookup(rule, "serviceAccounts.nameSelector.matchNames", [])

    if match_names:
        if service_account_name not in match_names:
            return False

    # Check for were label selector is provided and ensure that
    # all the labels to be matched exist on the target namespace.

    match_labels = lookup(rule, "serviceAccounts.labelSelector.matchLabels", {})

    if match_labels:
        labels = lookup(service_account_obj, "metadata.labels", {})
        for key, value in match_labels.items():
            if labels.get(key) != value:
                return False

    # Check for where label selector is provided but with more
    # general match expressions. Ensure that all the expressions
    # match the labels on the target service account.

    match_expressions = lookup(
        rule, "serviceAccounts.labelSelector.matchExpressions", []
    )

    if match_expressions:
        service_account_labels = lookup(service_account_obj, "metadata.labels", {})
        for item in match_expressions:
            key = item["key"]
            operator = item["operator"]
            values = item.get("values", [])
            value = service_account_labels.get(key)
            if operator == "In":
                if values:
                    if value is None or value not in values:
                        return False
            elif operator == "NotIn":
                if values:
                    if value is not None and value in values:
                        return False
            elif operator == "Exists":
                if key not in service_account_labels:
                    return False
            elif operator == "DoesNotExist":
                if key in service_account_labels:
                    return False

    return True


def reconcile_config(config_name, config_obj):
    """Perform reconciliation for the specified config."""

    api = pykube.HTTPClient(pykube.KubeConfig.from_env())

    namespace_query = pykube.Namespace.objects(api)

    for namespace_item in namespace_query:
        rules = list(
            matches_target_namespace(
                namespace_item.name, namespace_item.obj, [config_obj]
            )
        )

        for rule in rules:
            reconcile_namespace(namespace_item.name, rule)


def reconcile_secret(secret_name, namespace_name, secret_obj):
    """Perform reconciliation for the specified secret."""

    api = pykube.HTTPClient(pykube.KubeConfig.from_env())

    try:
        namespace_item = pykube.Namespace.objects(api).get(name=namespace_name)
    except pykube.exceptions.ObjectDoesNotExist as e:
        return

    rules = list(matches_target_namespace(namespace_name, namespace_item.obj))

    for rule in rules:
        if matches_source_secret(secret_name, secret_obj, rule):
            service_account_query = pykube.ServiceAccount.objects(api).filter(
                namespace=namespace_name
            )

            for service_account_item in service_account_query:
                if matches_service_account(
                    service_account_item.name, service_account_item.obj, rule
                ):
                    inject_secret(namespace_name, secret_name, service_account_item)


def reconcile_namespace(namespace_name, rule):
    """Applies the injection rule for the specified namespace."""

    api = pykube.HTTPClient(pykube.KubeConfig.from_env())

    # Need to list the secrets in the namespace and see if any match
    # the rule. If they do, then we see if there is a service account
    # that matches the rule which the secret should be injected into.

    secrets_query = pykube.Secret.objects(api).filter(namespace=namespace_name)

    for secret_item in secrets_query:
        if matches_source_secret(secret_item.name, secret_item.obj, rule):
            service_account_query = pykube.ServiceAccount.objects(api).filter(
                namespace=namespace_name
            )

            for service_account_item in service_account_query:
                if matches_service_account(
                    service_account_item.name, service_account_item.obj, rule
                ):
                    inject_secret(
                        namespace_name,
                        secret_item.name,
                        secret_item.obj.get("type"),
                        service_account_item,
                    )


def inject_secret(namespace_name, secret_name, secret_type, service_account_item):
    """Inject the name of the secret into the service account as an image
    pull secret or as other secret if it is necessary.

    """

    if secret_type == "kubernetes.io/dockerconfigjson":
        secrets_key = "imagePullSecrets"
    else:
        secrets_key = "secrets"

    # First check if already in the service account, in which case
    # can bail out straight away.

    secrets = service_account_item.obj.get(secrets_key, [])

    if {"name": secret_name} in secrets:
        return

    # Now need to update the existing service account to add in the
    # name of the secret.

    secrets.append({"name": secret_name})

    service_account_item.obj[secrets_key] = secrets

    try:
        service_account_item.update()

    except pykube.exceptions.KubernetesError as e:
        get_logger().warning(
            f"Service account {service_account_item.name} in namespace {namespace_name} couldn't be updated."
        )

    else:
        get_logger().info(
            f"Injected secret {secret_name} into service account {service_account_item.name} in namespace {namespace_name}."
        )
