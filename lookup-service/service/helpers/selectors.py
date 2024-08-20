"""Selectors for matching Kubernetes resource objects."""

import fnmatch
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List

from ..helpers.objects import xgetattr


@dataclass
class NameSelector:
    """Selector for matching Kubernetes resource objects by name."""

    match_names: List[str]

    def match_resource(self, resource: Dict[str, Any]) -> bool:
        """Check if a resource matches the selector. Note that if the list of
        names is empty, then the selector will match all resources. When
        matching names we actually use a glob expression."""

        if not self.match_names:
            return True

        name = xgetattr(resource, "metadata.name")

        for pattern in self.match_names:
            if fnmatch.fnmatch(name, pattern):
                return True

        return False


class Operator(Enum):
    """Operators for when matching Kubernetes resource objects by label
    expressions.
    """

    IN = "In"
    NOT_IN = "NotIn"
    EXISTS = "Exists"
    DOES_NOT_EXIST = "DoesNotExist"


@dataclass
class LabelSelectorRequirement:
    """Selector for matching Kubernetes resource objects by label express."""

    key: str
    operator: Operator
    values: List[str]

    def match_resource(self, resource: Dict[str, Any]) -> bool:
        """Check if a resource matches the selector."""

        labels = xgetattr(resource, "metadata.labels", {})

        value = labels.get(self.key)

        if self.operator == Operator.IN:
            return value in self.values
        elif self.operator == Operator.NOT_IN:
            return value not in self.values
        elif self.operator == Operator.EXISTS:
            return value is not None
        elif self.operator == Operator.DOES_NOT_EXIST:
            return value is None

        return False


@dataclass
class LabelSelector:
    """selector for matching Kubernetes resource objects by label."""

    match_labels: Dict[str, str]
    match_expressions: List[LabelSelectorRequirement]

    def match_resource(self, resource: Dict[str, Any]) -> bool:
        """Check if a resource matches the selector."""

        # First check if labels match by key/value pairs. If the set of labels
        # is empty, then the selector will match all resources, but will still
        # need to go on and check the label expressions.

        labels = xgetattr(resource, "metadata.labels", {})

        if not all(
            labels.get(key) == value for key, value in self.match_labels.items()
        ):
            return False

        # Now check list of label expressions. If this list is empty, then it
        # will match all resources.

        return all(expr.match_resource(resource) for expr in self.match_expressions)


def convert_to_name_selector(name_selector_dict: dict) -> NameSelector:
    """Converts a Kubernetes resource representation of a name selector to a
    NameSelector object.
    """

    return NameSelector(match_names=name_selector_dict.get("matchNames", []))


def convert_to_label_selector(label_selector_dict: dict) -> LabelSelector:
    """Converts a Kubernetes resource representation of a label selector to a
    LabelSelector object.
    """

    match_labels = label_selector_dict.get("matchLabels", {})

    match_expressions_data = label_selector_dict.get("matchExpressions", [])

    match_expressions = [
        LabelSelectorRequirement(
            key=expr["key"],
            operator=Operator(expr["operator"]),
            values=expr.get("values"),
        )
        for expr in match_expressions_data
    ]

    return LabelSelector(match_labels=match_labels, match_expressions=match_expressions)


@dataclass
class ResourceSelector:
    """Selectors for matching Kubernetes resource objects."""

    name_selector: NameSelector
    label_selector: LabelSelector

    def __init__(self, selector: Any) -> None:
        self.name_selector = convert_to_name_selector(selector.get("nameSelector", {}))
        self.label_selector = convert_to_label_selector(
            selector.get("labelSelector", {})
        )

    def match_resource(self, resource: Dict[str, Any]) -> bool:
        """Check if a resource matches the selector."""

        return self.name_selector.match_resource(
            resource
        ) and self.label_selector.match_resource(resource)
