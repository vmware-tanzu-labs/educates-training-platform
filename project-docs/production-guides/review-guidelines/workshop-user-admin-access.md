Workshop user admin access
==========================

By default workshop users will have admin role within their session namespaces if granted access to the cluster. They do not have the ability to perform cluster admin actions on the Kubernetes cluster itself.

A workshop user could be granted cluster admin access by [overriding the default RBAC rules](overriding-default-rbac-rules) but this should never be allowed for workshops running in shared clusters where public or untrusted users can access the workshop.

Cluster admin access should only ever be used where a workshop is being run by a user themselves on their own cluster running on their local machine, with their own workshops.

The obvious risk of a workshop granting cluster admin access is that the user has access they shouldn't otherwise and if it is a shared cluster they could interfere with other users, access secret information, or break the cluster itself.

If a workshop does require a level of cluster admin access, then virtual clusters could instead be used. A virtual cluster will provide each workshop user their own separate Kubernetes cluster with cluster admin access. This will allow them to perform operations within the cluster as an admin, but they will still not be able to access the underlying UNIX system nodes, or reconfigure the Kubernetes control plane.

**Recommendations**

* Ensure that workshops do not give the workshop user cluster admin access.
* Ensure that cluster admin access or other elevated privileges is never given to service accounts in session namespaces the workshop user can access.
* Use a virtual cluster if a workshop needs to demonstrate functions requiring cluster admin access.
