from .helpers import xget

from .operator_config import OPERATOR_API_GROUP, CLUSTER_STORAGE_GROUP


def vcluster_workshop_spec_patches(application_properties):
    return {
        "spec": {
            "session": {
                "namespaces": {
                    "security": {"token": {"enabled": False}, "policy": "baseline"}
                },
                "applications": {"console": {"vendor": "octant"}},
                "variables": [
                    {
                        "name": "vcluster_secret",
                        "value": "$(session_namespace)-vc-kubeconfig",
                    },
                ],
            }
        }
    }


def vcluster_environment_objects_list(application_properties):
    return []


def vcluster_session_objects_list(application_properties):
    budget = xget(application_properties, "budget", "custom")
    policy = xget(application_properties, "security.policy", "baseline")

    syncer_memory = xget(application_properties, "resources.syncer.memory", "1Gi")
    k3s_memory = xget(application_properties, "resources.k3s.memory", "2Gi")

    syncer_storage = xget(application_properties, "resources.syncer.storage", "5Gi")

    objects = [
        {
            "apiVersion": "v1",
            "kind": "Namespace",
            "metadata": {
                "name": "$(session_namespace)-vc",
                "annotations": {
                    "secretgen.carvel.dev/excluded-from-wildcard-matching": "",
                    f"training.{OPERATOR_API_GROUP}/session.role": "custom",
                    f"training.{OPERATOR_API_GROUP}/session.budget": budget,
                    f"training.{OPERATOR_API_GROUP}/session.policy": policy,
                },
            },
        },
        {
            "apiVersion": f"secrets.{OPERATOR_API_GROUP}/v1beta1",
            "kind": "SecretCopier",
            "metadata": {"name": "$(session_namespace)-vc-kubeconfig"},
            "spec": {
                "rules": [
                    {
                        "sourceSecret": {
                            "name": "$(session_namespace)-vc-kubeconfig",
                            "namespace": "$(session_namespace)-vc",
                        },
                        "targetNamespaces": {
                            "nameSelector": {"matchNames": ["$(workshop_namespace)"]}
                        },
                        "targetSecret": {"name": "$(vcluster_secret)"},
                        "reclaimPolicy": "Delete",
                    }
                ]
            },
        },
        {
            "apiVersion": "v1",
            "kind": "ServiceAccount",
            "metadata": {
                "name": "vc-my-vcluster",
                "namespace": "$(session_namespace)-vc",
            },
        },
        {
            "apiVersion": "rbac.authorization.k8s.io/v1",
            "kind": "ClusterRole",
            "metadata": {
                "name": "my-vcluster-$(session_namespace)-vc",
            },
            "rules": [
                {
                    "apiGroups": ["storage.k8s.io"],
                    "resources": ["storageclasses"],
                    "verbs": ["get", "list", "watch"],
                },
            ],
        },
        {
            "apiVersion": "rbac.authorization.k8s.io/v1",
            "kind": "Role",
            "metadata": {
                "name": "my-vcluster",
                "namespace": "$(session_namespace)-vc",
            },
            "rules": [
                {
                    "apiGroups": [""],
                    "resources": [
                        "configmaps",
                        "secrets",
                        "services",
                        "pods",
                        "pods/attach",
                        "pods/portforward",
                        "pods/exec",
                        "endpoints",
                        "persistentvolumeclaims",
                    ],
                    "verbs": [
                        "create",
                        "delete",
                        "patch",
                        "update",
                        "get",
                        "list",
                        "watch",
                    ],
                },
                {
                    "apiGroups": [""],
                    "resources": ["events", "pods/log"],
                    "verbs": ["get", "list", "watch"],
                },
                {
                    "apiGroups": ["networking.k8s.io"],
                    "resources": ["ingresses"],
                    "verbs": [
                        "create",
                        "delete",
                        "patch",
                        "update",
                        "get",
                        "list",
                        "watch",
                    ],
                },
                {
                    "apiGroups": ["apps"],
                    "resources": ["statefulsets", "replicasets", "deployments"],
                    "verbs": ["get", "list", "watch"],
                },
            ],
        },
        {
            "apiVersion": "rbac.authorization.k8s.io/v1",
            "kind": "RoleBinding",
            "metadata": {
                "name": "my-vcluster",
                "namespace": "$(session_namespace)-vc",
            },
            "subjects": [
                {
                    "kind": "ServiceAccount",
                    "name": "vc-my-vcluster",
                    "namespace": "$(session_namespace)-vc",
                }
            ],
            "roleRef": {
                "kind": "Role",
                "name": "my-vcluster",
                "apiGroup": "rbac.authorization.k8s.io",
            },
        },
        {
            "apiVersion": "rbac.authorization.k8s.io/v1",
            "kind": "Role",
            "metadata": {
                "name": "my-vcluster",
                "namespace": "$(session_namespace)",
            },
            "rules": [
                {
                    "apiGroups": [""],
                    "resources": [
                        "configmaps",
                        "secrets",
                        "services",
                        "pods",
                        "pods/attach",
                        "pods/portforward",
                        "pods/exec",
                        "endpoints",
                        "persistentvolumeclaims",
                    ],
                    "verbs": [
                        "create",
                        "delete",
                        "patch",
                        "update",
                        "get",
                        "list",
                        "watch",
                    ],
                },
                {
                    "apiGroups": [""],
                    "resources": ["events", "pods/log"],
                    "verbs": ["get", "list", "watch"],
                },
                {
                    "apiGroups": ["networking.k8s.io"],
                    "resources": ["ingresses"],
                    "verbs": [
                        "create",
                        "delete",
                        "patch",
                        "update",
                        "get",
                        "list",
                        "watch",
                    ],
                },
                {
                    "apiGroups": ["apps"],
                    "resources": ["statefulsets", "replicasets", "deployments"],
                    "verbs": ["get", "list", "watch"],
                },
            ],
        },
        {
            "apiVersion": "rbac.authorization.k8s.io/v1",
            "kind": "RoleBinding",
            "metadata": {
                "name": "my-vcluster",
                "namespace": "$(session_namespace)",
            },
            "subjects": [
                {
                    "kind": "ServiceAccount",
                    "name": "vc-my-vcluster",
                    "namespace": "$(session_namespace)-vc",
                }
            ],
            "roleRef": {
                "kind": "Role",
                "name": "my-vcluster",
                "apiGroup": "rbac.authorization.k8s.io",
            },
        },
        {
            "apiVersion": "rbac.authorization.k8s.io/v1",
            "kind": "ClusterRoleBinding",
            "metadata": {
                "name": "my-vcluster-$(session_namespace)-vc",
            },
            "subjects": [
                {
                    "kind": "ServiceAccount",
                    "name": "vc-my-vcluster",
                    "namespace": "$(session_namespace)-vc",
                }
            ],
            "roleRef": {
                "kind": "ClusterRole",
                "name": "my-vcluster-$(session_namespace)-vc",
                "apiGroup": "rbac.authorization.k8s.io",
            },
        },
        {
            "apiVersion": "v1",
            "kind": "Service",
            "metadata": {
                "name": "my-vcluster",
                "namespace": "$(session_namespace)-vc",
            },
            "spec": {
                "type": "ClusterIP",
                "ports": [
                    {
                        "name": "https",
                        "port": 443,
                        "targetPort": 8443,
                        "protocol": "TCP",
                    }
                ],
                "selector": {"app": "vcluster"},
            },
        },
        {
            "apiVersion": "v1",
            "kind": "Service",
            "metadata": {
                "name": "my-vcluster-headless",
                "namespace": "$(session_namespace)-vc",
            },
            "spec": {
                "ports": [
                    {
                        "name": "https",
                        "port": 443,
                        "targetPort": 8443,
                        "protocol": "TCP",
                    }
                ],
                "clusterIP": "None",
                "selector": {"app": "vcluster"},
            },
        },
        {
            "apiVersion": "apps/v1",
            "kind": "StatefulSet",
            "metadata": {
                "name": "my-vcluster",
                "namespace": "$(session_namespace)-vc",
            },
            "spec": {
                "serviceName": "my-vcluster-headless",
                "replicas": 1,
                "selector": {"matchLabels": {"app": "vcluster"}},
                "volumeClaimTemplates": [
                    {
                        "metadata": {"name": "data"},
                        "spec": {
                            "accessModes": ["ReadWriteOnce"],
                            "storageClassName": None,
                            "resources": {"requests": {"storage": syncer_storage}},
                        },
                    }
                ],
                "template": {
                    "metadata": {"labels": {"app": "vcluster"}},
                    "spec": {
                        "terminationGracePeriodSeconds": 10,
                        "nodeSelector": {},
                        "affinity": {},
                        "tolerations": [],
                        "serviceAccountName": "vc-my-vcluster",
                        "volumes": [],
                        "securityContext": {
                            "fsGroup": CLUSTER_STORAGE_GROUP,
                            "supplementalGroups": [CLUSTER_STORAGE_GROUP],
                        },
                        "containers": [
                            {
                                "image": "rancher/k3s:v1.23.3-k3s1",
                                "name": "vcluster",
                                "command": ["/bin/sh"],
                                "args": [
                                    "-c",
                                    "/bin/k3s server --write-kubeconfig=/data/k3s-config/kube-config.yaml --data-dir=/data --disable=traefik,servicelb,metrics-server,local-storage,coredns --disable-network-policy --disable-agent --disable-scheduler --disable-cloud-controller --flannel-backend=none --kube-controller-manager-arg=controllers=*,-nodeipam,-nodelifecycle,-persistentvolume-binder,-attachdetach,-persistentvolume-expander,-cloud-node-lifecycle --service-cidr=10.96.0.0/12 && true",
                                ],
                                "env": [],
                                "securityContext": {
                                    "allowPrivilegeEscalation": False,
                                    "runAsNonRoot": True,
                                    "runAsUser": 12345,
                                },
                                "volumeMounts": [
                                    {"mountPath": "/data", "name": "data"}
                                ],
                                "resources": {
                                    "limits": {"memory": k3s_memory},
                                    "requests": {"cpu": "200m", "memory": k3s_memory},
                                },
                            },
                            {
                                "name": "syncer",
                                "image": "loftsh/vcluster:0.7.1",
                                "args": [
                                    "--name=my-vcluster",
                                    "--target-namespace=$(session_namespace)",
                                    "--tls-san=my-vcluster.$(session_namespace)-vc.svc.cluster.local",
                                    "--out-kube-config-server=https://my-vcluster.$(session_namespace)-vc.svc.cluster.local",
                                    "--out-kube-config-secret=$(session_namespace)-vc-kubeconfig",
                                    "--sync=legacy-storageclasses",
                                ],
                                "livenessProbe": {
                                    "httpGet": {
                                        "path": "/healthz",
                                        "port": 8443,
                                        "scheme": "HTTPS",
                                    },
                                    "failureThreshold": 10,
                                    "initialDelaySeconds": 60,
                                    "periodSeconds": 2,
                                },
                                "readinessProbe": {
                                    "httpGet": {
                                        "path": "/readyz",
                                        "port": 8443,
                                        "scheme": "HTTPS",
                                    },
                                    "failureThreshold": 30,
                                    "periodSeconds": 2,
                                },
                                "securityContext": {
                                    "allowPrivilegeEscalation": False,
                                    "runAsNonRoot": True,
                                    "runAsUser": 12345,
                                },
                                "env": [],
                                "volumeMounts": [
                                    {
                                        "mountPath": "/data",
                                        "name": "data",
                                        "readOnly": True,
                                    }
                                ],
                                "resources": {
                                    "limits": {"memory": syncer_memory},
                                    "requests": {
                                        "cpu": "100m",
                                        "memory": syncer_memory,
                                    },
                                },
                            },
                        ],
                    },
                },
            },
        },
    ]
    return objects


def vcluster_pod_template_spec_patches(application_properties):
    return {
        "containers": [
            {
                "name": "workshop",
                "volumeMounts": [
                    {"name": "kubeconfig", "mountPath": "/opt/kubeconfig"}
                ],
            }
        ],
        "volumes": [
            {
                "name": "kubeconfig",
                "secret": {"secretName": "$(vcluster_secret)"},
            }
        ],
    }
