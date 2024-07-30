"""Configuration database for target clusters."""

from dataclasses import dataclass

from typing import Any, Dict, List


@dataclass
class ClusterConfig:
    """Configuration object for a target cluster."""

    name: str
    uid: str
    labels: Dict[str, str]
    kubeconfig: Dict[str, Any]


@dataclass
class ClusterDatabase:
    """Database for storing cluster configurations. Clusters are stored in a
    dictionary with the cluster's name as the key and the cluster configuration
    object as the value."""

    clusters: Dict[str, ClusterConfig]

    def __init__(self) -> None:
        self.clusters = {}

    def add_cluster(self, cluster: ClusterConfig) -> None:
        """Add the cluster to the database."""

        self.clusters[cluster.name] = cluster

    def remove_cluster(self, name: str) -> None:
        """Remove a cluster from the database."""

        self.clusters.pop(name, None)

    def get_clusters(self) -> List[ClusterConfig]:
        """Retrieve a list of clusters from the database."""

        return list(self.clusters.values())

    def get_cluster_names(self) -> List[str]:
        """Retrieve a list of cluster names from the database."""

        return list(self.clusters.keys())

    def get_cluster_by_name(self, name: str) -> ClusterConfig:
        """Retrieve a cluster from the database by name."""

        return self.clusters.get(name)
