Workshop container CPU
======================

By default the workshop session container does not specify any resource requirement for CPU. This in general works fine as work done from the terminal in the workshop container is not usually CPU intensive or is short lived. In the event that many workshop sessions do run on the same node and they are all running CPU intensive tasks at the same time, what will happen is that Kubernetes will limit all CPU usage by the workshop container in proportion to others. As a result, it shouldn't be possible for any one container to completely monopolise the available CPU requirements as all will be limited as they don't specify a CPU requirement and thus CPU is provided as best effort.

It is possible that this default strategy may not always work and the user experience could be less than optimal when the number of current workshop sessions is scaled up.

A problematic case may be one where a workshop session runs commands from the terminal which are CPU intensive and long running (eg., GraalVM compilation). In this case were lots of workshop sessions scheduled to the same node and the CPU intensive periods overlap, they could starve each other for CPU and slow things down notably.

In this case it would be recommended to run such a workshop on its own cluster with high CPU instance types for the nodes, and not have different workshops run on the same cluster. Further, a pod template [patch](patching-workshop-deployment) should be applied to the workshop container in order to specify a CPU request and limit so they get a guaranteed amount of CPU, but at the same time are also limited at the top end of how much they can use.

```yaml
spec:
  session:
    patches:
      containers:
      - name: workshop
        resources:
          requests:
            cpu: "500m"
          limits:
            cpu: "1000m"
```

**Recommendations**

* Ensure that workshops with high CPU requirements for extended periods of time run on their own clusters with high CPU instance types for nodes.
* Ensure that workshops with high CPU requirements for extended periods of time specify request/limit values for CPU on the workshop container.
