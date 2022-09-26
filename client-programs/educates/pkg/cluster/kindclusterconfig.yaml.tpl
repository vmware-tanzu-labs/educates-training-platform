kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
nodes:
- role: control-plane
  kubeadmConfigPatches:
  - |
    kind: InitConfiguration
    nodeRegistration:
      kubeletExtraArgs:
        node-labels: "ingress-ready=true"
  {{- if eq .ClusterSecurity.PolicyEngine "pod-security-policies" }}
  - |
    kind: ClusterConfiguration
    metadata:
      name: config
    apiServer:
      extraArgs:
        enable-admission-plugins: PodSecurityPolicy
  {{- end }}
  extraPortMappings:
  - containerPort: 80
    {{- if .BindIP }}
    listenAddress: {{ .BindIP }}
    {{- end }}
    hostPort: 80
    protocol: TCP
  - containerPort: 443
    {{- if .BindIP }}
    listenAddress: {{ .BindIP }}
    {{- end }}
    hostPort: 443
    protocol: TCP
containerdConfigPatches:
- |-
  [plugins."io.containerd.grpc.v1.cri".registry.mirrors."registry.default.svc.cluster.local:5001"]
    endpoint = ["http://educates-registry:5000"]
{{- if eq .ClusterSecurity.PolicyEngine "pod-security-standards" }}
featureGates:
  PodSecurity: true
{{ end }}
