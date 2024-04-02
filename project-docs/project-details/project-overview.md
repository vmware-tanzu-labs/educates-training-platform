Project Overview
================

The Educates project is designed to provide a platform for hosting workshops. It was primarily created to support the work of a team of developer advocates who needed to train users in using Kubernetes and show case developer tools or applications running on Kubernetes.

Although the principal deployment platform for Educates is Kubernetes, and is being used to teach users about Kubernetes, it could also be used to host training for other purposes as well. It may for example be used to help train users in web based applications, use of databases, or programming languages, where the user has no interest or need for Kubernetes.

Latest project version
----------------------

The latest release of Educates is version 2.7.0.

Source code repositories
------------------------

The source code repository for the Educates training platform can be found at:

* [https://github.com/vmware-tanzu-labs/educates-training-platform](https://github.com/vmware-tanzu-labs/educates-training-platform)

Getting help with Educates
--------------------------

If you have questions about using Educates, use the `#educates` channel under
the [Kubernetes community Slack](https://kubernetes.slack.com/).

If you have found a bug in Educates or want to request a feature, you can use
our [GitHub issue
tracker](https://github.com/vmware-tanzu-labs/educates-training-platform/issues).

Overall goals of the project
----------------------------

Being born out of the requirements of a group of developer advocates, the use case scenarios which Educates has been designed to support are as follows.

* Supervised workshops. This could be a workshop run at a conference, at a customer site, or purely online. The workshop has a set time period and you know the maximum number of users to expect. Once the training has completed, the Kubernetes cluster created for the workshop would be destroyed.

* Temporary learning portal. This is where you need to provide access to a small set of workshops of short duration for use as hands on demos at a conference vendor booth. Users would select which topic they want to learn about and do that workshop. The workshop instance would be created on demand. When they have finished the workshop, that workshop instance would be destroyed to free up resources. Once the conference had finished, the Kubernetes cluster would be destroyed.

* Permanent learning portal. Similar to the temporary learning portal, but would be run on an extended basis as a public web site where anyone could come and learn at any time.

* Personal training or demos. This is where anyone wants to run a workshop on their own Kubernetes cluster to learn that topic, or where a product demo was packaged up as a workshop and they want to use it to demonstrate the product to a customer. The workshop environment can be destroyed when complete, but there is no need for the cluster to be destroyed.

When deploying Educates to Kubernetes, the intent was that whenever possible a shared Kubernetes cluster would be used so as to reduce the amount of set up required. This works for developer focused workshops where access to only a single namespace is required, as it is usually not necessary to provide elevated access to the Kubernetes cluster, and role based access controls (RBAC) can be used to prevent users from interfering with each other. Quotas can also be set so that users are restricted to how much resources they can use.

In the case of needing to run workshops which deal with cluster operations, for which users need cluster admin access, a separate virtual cluster hosted in the same Kubernetes cluster can if necessary be enabled for a workshop session. You could instead also make use of custom resource types created from a workshop session to startup virtual machines using KubeVirt if needing a complete Linux environment with administrator access, or you could use a custom resource to request access to complete but separate Kubernetes clusters available from a separate infrastructure service.

In catering for the scenarios listed above, the set of primary requirements related to creation of workshop content, and what could be done at run time were as follows.

* Everything for a workshop needed to be able to be stored in a Git repository, with no dependency on using a special web application or service to create a workshop.

* Use of a hosted Git repository or an image registry as a means to distribute workshop content.

* The instructions for a user to follow to do the workshop would be provided as Markdown or AsciiDoc files.

* Instructions can be annotated as executable commands so that when clicked on in the workshop dashboard they can be automatically executed for the user in the appropriate terminal to avoid mistakes when commands are entered manually.

* Text can be annotated as copyable so that when clicked on in the workshop dashboard it would be copied into the browser paste buffer ready for pasting into the terminal or other web application.

* Each user is provided access to one or more namespaces in the Kubernetes cluster unique to their session. For Kubernetes based workshops, this is where applications would be deployed as part of the workshop. 

* Additional Kubernetes resources specific to a workshop session can be pre-created when the session is started. This is to enable the deployment of applications for each user session.

* Additional Kubernetes resources common to all workshop sessions are able to be deployed when the workshop environment is first created. This is to enable deployment of shared applications used by all users.

* Application of resource quotas on each workshop session to control how much resources users can consume.

* Application of role based access control (RBAC) on each workshop session to control what users can do.

* Ability to provide access to an editor (IDE) in the workshop dashboard in the web browser for users to use to edit files during the workshop.

* Ability to provide access to a web based console for accessing the Kubernetes cluster.

* Ability to integrate additional web based applications into the workshop dashboard specific to the topic of the workshop.

* Ability for the workshop dashboard to display slides used by an instructor in support of the workshop.

Over time the capabilities of the platform have been greatly expanded from this intial core set of requirements, so refer to other parts of the documentation for more information.

Platform architectural overview
-------------------------------

The Educates platform relies on a Kubernetes operator to perform the bulk of the work. The actions of the operator are controlled through a set of custom resources specific to the Educates platform.

There are multiple ways of using the custom resources to deploy workshops. The primary way is to create a training portal, which in turn then triggers the setup of one or more workshop environments, one for each distinct workshop. When users access the training portal and select the workshop they wish to do, the training portal allocates to that user a workshop session (creating one if necessary) against the appropriate workshop environment, and the user is redirected to that workshop session instance.

![](architectural-overview.png)

Each workshop session can be associated with one or more Kubernetes namespaces specifically for use during that session. Role based access control (RBAC) applied to the unique Kubernetes service account for that session, ensures that the user can only access the namespaces and other resources that they are allowed to for that workshop.

In this scenario, the custom resource types that come into play are:

* ``Workshop`` - Provides the definition of a workshop. Preloaded by an administrator into the cluster, it defines where the workshop content is hosted, or the location of a container image which bundles the workshop content and any additional tools required for the workshop. The definition also lists additional resources that should be created which are to be shared between all workshop sessions, or for each session, along with details of resources quotas and access roles required by the workshop.

* ``TrainingPortal`` - Created by an administrator in the cluster to trigger the deployment of a training portal. The training portal can provide access to one or more distinct workshops defined by a ``Workshop`` resource. The training portal provides a web based interface for registering for workshops and accessing them. It also provides a REST API for requesting access to workshops, allowing custom front ends to be created which integrate with separate identity providers and which provide an alternate means for browsing and accessing workshops.

* ``WorkshopEnvironment`` - Used by the training portal to trigger the creation of a workshop environment for a workshop. This causes the operator to setup a namespace for the workshop into which shared resources can be deployed, and where the workshop sessions are run.

* ``WorkshopSession`` - Used by the training portal to trigger the creation of a workshop session against a specific workshop environment. This causes the operator to setup any namespaces specific to the workshop session and pre-create additional resources required for a workshop session. Workshop sessions can be created up front in reserve, to be handed out when requested, or they can be created on demand.

Although the primary API for deploying a workshop environment are the Kubernetes resources, a command line client for Educates is provided which hides many of the details for typical deployments. The Educates command line client simplifies local deployment for working on Educates workshop content and although it could be used with a hosted Kubernetes cluster, power users will still likely want to work directly with the Kubernetes resources to manage an Educates deployment.
