Project Overview
================

The educates project is designed to provide a platform for hosting workshops. It was primarily created to support the work of a team of developer advocates who needed to train users in using Kubernetes and show case developer tools or applications running on Kubernetes.

Although educates requires Kubernetes to run, and is being used to teach users about Kubernetes, it could also be used to host training for other purposes as well. It may for example be used to help train users in web based applications, use of databases, or programming languages, where the user has no interest or need for Kubernetes.

Overall goals of the project
----------------------------

Being born out of the requirements of a group of developer advocates, the use case scenarios which educates has been designed to support are as follows.

* Supervised workshops. This could be a workshop run at a conference, at a customer site, or purely online. The workshop has a set time period and you know the maximum number of users to expect. Once the training has completed, the Kubernetes cluster created for the workshop would be destroyed.

* Temporary learning portal. This is where you need to provide access to a small set of workshops of short duration for use as hands on demos at a conference vendor booth. Users would select which topic they want to learn about and do that workshop. The workshop instance would be created on demand. When they have finished the workshop, that workshop instance would be destroyed to free up resources. Once the conference had finished, the Kubernetes cluster would be destroyed.

* Permanent learning portal. Similar to the temporary learning portal, but would be run on an extended basis as a public web site where anyone could come and learn at any time.

* Personal training or demos. This is where anyone wants to run a workshop on their own Kubernetes cluster to learn that topic, or where a product demo was packaged up as a workshop and they want to use it to demonstrate the product to a customer. The workshop environment can be destroyed when complete, but there is no need for the cluster to be destroyed.

When running workshops, where ever possible a shared Kubernetes cluster would be used so as to reduce the amount of set up required. This works for developer focused workshops as it is usually not necessary to provide elevated access to the Kubernetes cluster, and role based access controls (RBAC) can be used to prevent users from interfering with each other. Quotas can also be set so that users are restricted to how much resources they can use.

In the case of needing to run workshops which deal with cluster operations, for which users need cluster admin access, a separate cluster would be created for each user. This project doesn't deal with provisioning clusters, only with deploying a workshop environment in a cluster once it exists.

In catering for the scenarios listed above, the set of primary requirements related to creation of workshop content, and what could be done at run time were as follows.

* Everything for a workshop needed to be able to be stored in a Git repository, with no dependency on using a special web application or service to create a workshop.

* Use of GitHub as a means to distribute workshop content. Alternatively, optional distribution of a workshop as a container image. The latter also being necessary if special tools need to be installed for use in a workshop.

* The instructions for a user to follow to do the workshop would be provided as Markdown or AsciiDoc files.

* Instructions can be annotated as executable commands so that when clicked on in the workshop dashboard they can be automatically executed for the user in the appropriate terminal to avoid mistakes when commands are entered manually.

* Text can be annotated as copyable so that when clicked on in the workshop dashboard it would be copied into the browser paste buffer ready for pasting into the terminal or other web application.

* Each user is provided access to one or more namespaces in the Kubernetes cluster unique to their session. For Kubernetes based workshops, this is where applications would be deployed as part of the workshop.

* Additional Kubernetes resources specific to a workshop session can be pre-created when the session is started. This is to enable the deployment of applications for each user session.

* Additional Kubernetes resources common to all workshop sessions are able to be deployed when the workshop environment is first created. This is to enable deployment of shared applications used by all users.

* Application of resource quotas on each workshop session to control how much resources users can consume.

* Application of role based access control (RBAC) on each workshop session to control what users can do.

* Ability to provide access to an editor (IDE) in the workshop dashboard in the web browser for users to use to edit files during the workshop.

* Ability to provide access to a web based console for accessing the Kubernetes cluster. Use of the Kubernetes dashboard or Octant is suported.

* Ability to integrate additional web based applications into the workshop dashboard specific to the topic of the workshop.

* Ability for the workshop dashboard to display slides used by an instructor in support of the workshop.

Platform architectural overview
-------------------------------

The educates platform relies on a Kubernetes operator to perform the bulk of the work. The actions of the operator are controlled through a set of custom resources specific to the educates platform. The custom resources are:

* ``Workshop`` - Provides the definition of a workshop. This defines where the workshop content is hosted, or the location of container image which bundles the workshop content and any additional tools required for the workshop. The definition also lists additional resources that should be created which are to be shared between all workshop sessions, or for each session, along with details of resources quotas and access roles required by the workshop.

* ``WorkshopEnvironment`` - Used to trigger the creation of a workshop environment for a specific workshop. This causes the operator to setup a namespace for the workshop into which shared resources can be deployed, and where the workshop dashboard instances are run.

* ``WorkshopSession`` - Used to trigger the creation of a workshop session against a specific workshop environment. This causes the operator to setup any namespaces specific to the workshop session and pre-create additional resources required for a workshop session.

* ``WorkshopRequest`` - A means for a non privileged user to trigger the creation of a workshop session. The ability to create this custom resource can be controlled through access roles. The definition of the workshop environment can also restrict what namespaces the creation of a workshop request will be recognised in, as well as require a secret token be known by the requestor.

* ``TrainingPortal`` - Used to trigger the deployment of a set of workshop environments and a web based training portal for registering for the workshops and accessing them.

* ``SystemProfile`` - Used to configure cluster wide defaults to be applied to the operator and workshop environments. This includes ingress domain name, ingress secret, ingress class, storage class and registry image pull secrets.

When needing to run workshops, the typical use case scenarios would see the ``TrainingPortal`` custom resource being used to drive the creation of the workshop environments and sessions. Thus you only need to know about it and the ``Workshop`` custom resource. Other custom resources would only come into play if wishing to create custom workshop deployment scenarios.

Current status of the project
-----------------------------

The educates project is the third incarnation of a system to support hosting workshops in conjunction with Kubernetes.

The first incarnation used a tool called Workshopper to provide workshop instructions, but where all work was still done from a users own local computer.

The second incarnation resulted in a tool being developed called Homeroom. This used JupyterHub to manage on demand creation of workshop sessions in Kubernetes, with work being done through the web browser in a container running in the Kubernetes cluster. Homeroom originally targeted just OpenShift, although the most recent versions provided some support for being deployed in other Kubernetes distributions.

This third incarnation dispenses with JupyterHub and instead use a Kubernetes operator to manage creation of workshop environments and sessions, with a separate web based training portal being used to mediate access and manage sessions.

At this point work has been completed to support all the use case scenarios listed above, although there still hasn't been an official announcement of availability of educates.

This shouldn't deter you from trying out educates. What is being done isn't new and is based on over 3 years of iterative improvements and learning in providing workshop based training.
