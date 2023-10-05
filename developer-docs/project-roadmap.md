Project Roadmap
===============

The Educates project uses a GitHub [project board](https://github.com/orgs/vmware-tanzu-labs/projects/13) to track issues and feature requests. For more substantial pie-in-the-sky goals, these are outlined below. Because something is listed here doesn't mean that it will actually be done. The list is just intended to capture ideas for larger changes or new features we think would be worthwhile doing at some point so you can see where the project may be heading.

Simplified course deployment
----------------------------

To deploy a workshop it is necessary to first load the workshop definition, and then deploy a training portal to host that workshop.

If you have multiple workshops, a single training portal can host all of the workshops, but you still need to load each workshop definition first.

The requirement to load the workshop definition first was done with the intention that it provides an opportunity for someone to review what the workshop requires before a workshop environment for it is created, and access provided.

The `educates` CLI provides a mechanism to deploy a workshop, including the loading of the workshop definition and creation of the training portal if required, in one command. You would though still need to run a command for each workshop to deploy it.

To better support deployment of a course consisting of multiple workshops, the idea is to introduce a new custom resource called `Course` which can be used to reference multiple locations where workshop definitions which go together to form a course are hosted. Along with this list would if necessary be parameters customizing capacity requirements etc, for each workshop.

The intent then would be that this single `Course` custom resource could be created in the cluster, and the corresponding operator would download all the workshop definitions, load them into the cluster and then create a training portal to host those workshops.

At the same time, new commands would be added to the `educates` CLI which uses this new capability to facilitate deployment of a course by just pointing at the location of the hosted course definition.

Rewrite of workshop dashboard
-----------------------------

A user undertaking a workshop is presented with a workshop dashboard consisting of the workshop instructions, along with embedded terminals, editor, Kubernetes web console etc. This workshop dashboard is currently implemented using Node.JS on the server.

Use of Node.JS results in a dashboard application process which can be quite memory hungry, as well as all the required source files and package dependencies taking up a non trivial amount of space in the workshop base image.

Along with this code for the dashboard application, there are also various shell scripts for managing initialization of the container environment for the workshop, including triggering the execution of setup scripts provided with a workshop.

To reduce both memory and storage requirements, the idea is to rewrite both the dashboard application and all the mechanics for initialization of the container environment as a Go code application.

The result of this would be that all the core functionality required to support the workshop dashboard and the container environment could be shipped as a single binary, simplifying how the workshop base image is built.

A further goal from this would be to package up this self contained workshop environment application binary as a package which could be applied to a container image as part of a Dev Container image build. The idea here being that it would make it possible to more easily create custom workshop base images using any base operating system image desired.

Use of Dev Container builds to create the workshop images would also allow for smaller workshop images where only the minimal set of tools required are included, or workshop images which have additional third party applications packages included, which wouldn't normally be available.

Workshop as a service platform
------------------------------

At present the model for deployment of workshops means that a single workshop environment would generally be tied to a specific set of workshop instructions. Thus if you wanted to be able to have workshop sessions which use different workshop instructions, a separate workshop definition and environment would be needed for each.

It is technically possible to create a single workshop definition in conjunction with a custom frontend portal for creating workshop sessions, where the source of workshop instructions are injected as request parameters when a workshop session is requested. In this way what workshop instructions are used can be tailored per workshop session.

Using this one could create a "workshop as a service" type platform in the style of the original Katacoda platform whereby a workshop author could through an account provide links to their workshop content, with users then being able to select a workshop to do, but where a workshop sessions runs in a common shared workshop environment for workshops with similar requirements, rather than needing to create a distinct workshop environment for every workshop.

So although a "workshop as a service" type platform is possible now, it is not as streamlined a process as it could be, and a custom frontend portal would need to be created. The idea thus is to make deploying such a platform easier, including the creation of a dedicated custom frontend portal with ability to hook into third party SSO providers, and an ability for workshop authors to register one or more workshops to be hosted.
