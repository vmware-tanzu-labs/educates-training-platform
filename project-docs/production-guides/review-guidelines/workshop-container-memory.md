Workshop container memory
=========================

By default the container the workshop environment is running in is allocated 512Mi. If the editor is enabled this is increased to 1Gi. This memory is guaranteed, and as such Kubernetes will reserve that amount of memory on the node for the instance when scheduling pods.

This amount of memory is inclusive of what you may need for any commands run from the command line. If doing code compilation (especially Java applications), you may need to increase the amount of memory dedicated to the workshop container. If the workshop uses the editor a lot, or the workshop encourages a workshop user to explore source code or other files supplied with the workshop, the memory required by the editor can keep growing, so keep that in consideration when deciding if the amount of memory needs to be increased. If you don't provide enough memory, then the editor or applications run from the command line could fail when they run out of memory.

Memory available to the workshop container is [overridden](overriding-the-memory-available) using the `session.resources.memory` setting in the workshop definition.

```yaml
spec:
  session:
    resources:
      memory: 2Gi
```

**Recommendations**

* Ensure that you do not enable the editor if it is not required.
* Ensure that you do not enable a Kubernetes web console if not required.
* Ensure you do analysis to determine the maximum amount of memory required by the workshop container and set the memory size appropriately.

**Related issues**

Note that if docker support is enabled and you are building/running containers within the workshop environment (not as deployments in the cluster), the memory allocation for dockerd is distinct from that for the workshop container and should not be counted in the above allocation.

Note that increasing the size of nodes in the Kubernetes cluster such that more memory is available per node is not necessarily recommended as the amount of persistent volumes that can be mounted on a node is generally limited and does not increase with the amount of memory the node has. As such, a general guideline is to use nodes with 32Gi of memory (rather than 64Gi), and add as many nodes as required to the Kubernetes cluster on that basis.

Note that the memory is guaranteed by setting the `request` resource value the same as the `limit` value in the workshop container of the Kubernetes deployment. Although scheduling will take this into consideration with Kubernetes aiming to place the deployment on a node in the cluster which is known to have enough memory, you can still have problems when a node autoscalar is enabled.

The issue with autoscalars is that if the resources of the node are not being sufficiently used, it may decide to evict anything deployed to the node forcing them to be redeployed on another node. An example of a Kubernetes cluster from by an IaaS provider which uses an autoscalar is GKE autopilot. The consequence of using a cluster with autoscaling enabled is that workshop sessions can be interrupted and a users work is lost, with them being returned to the beginning when the new deployment of the workshop container starts up again. For this reason you should not deploy Educates on clusters where an autoscalar is configured which can see the number of nodes being scaled down automatically.
