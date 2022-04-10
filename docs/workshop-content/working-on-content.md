Working on Content
==================

Workshop content will either be embedded in a custom workshop image, or downloaded from a Git repository or web server when the workshop session is created. To speed up the iterative loop of editing and testing a workshop when developing workshop content, there are a number of best practices you can use.

Disabling reserved sessions
---------------------------

An instance of a training portal should be used when developing content where reserved sessions are disabled.

```
apiVersion: training.eduk8s.io/v1alpha1
kind: TrainingPortal
metadata:
  name: lab-sample-workshop
spec:
  portal:
    sessions:
      maximum: 1
  workshops:
  - name: lab-sample-workshop
    reserved: 0
    expires: 120m
    orphaned: 15m
```

If you don't disable reserved sessions then a new session will always be created ready for the next workshop session when there is available capacity to do so. If you are modifying workshop content while testing the current workshop session, then terminate the session and start a new one it will pickup the reserved session, which will still have a copy of the old content.

By disabling reserved sessions a new workshop session will always be created on demand, ensuring the latest workshop content is used.

Note that there can be a slight delay in being able to create a new workshop as the existing workshop session will need to be shutdown first. The new workshop session may also take some time to start if an updated version of the workshop image has to be pulled down.

Live updates to the content
---------------------------

If workshop content is being downloaded from a Git repository or web server and you are only doing simple updates to workshop instructions, or scripts or files bundled with the workshop, you can update the content in place without needing to restart the workshop session. To perform an update, after you have pushed back any changes to the hosted Git repository or updated the content available via the web server, from the workshop session terminal run:

```
update-workshop
```

This command will download any workshop content from the Git repository or web server, unpack it into the live workshop session, and re-run any script files found in the ``workshop/setup.d`` directory.

If you want to see where the workshop content is being downloaded from, you can find the location by viewing the file:

```
~/.eduk8s/workshop-files.txt
```

The location saved in this file could be changed if for example it referenced a specific version of the workshop content and you wanted to test with a different version.

Once the workshop content has been updated you can reload the current page of the workshop instructions by clicking on the reload icon on the dashboard while holding down the shift key.

Note that if additional pages were added to the workshop instructions, or pages renamed, you will need to restart the workshop renderer process. This can be done by running:

```
restart-workshop
```

So long as you didn't rename the current page, you can trigger a reload of the current page, or if the name had changed, click on the home icon (so long as name of the first page hadn't changed), or refresh the whole browser window.

If action blocks within the workshop instructions are broken and you wanted to make a change to the workshop instructions within the live workshop session to test, edits can be made to the appropriate page under ``/opt/workshop/content``. Navigate to the modified page or reload it to verify the change.

If wanting to make a change to setup scripts which create files specific to a workshop session and re-run them, make the edit to the script under ``/opt/workshop/setup.d``. To trigger running of any setup scripts, then run:

```
rebuild-workshop
```

If local changes to the workshop session check out okay then you can modify the file back in the original Git repository where you are keeping content.

Note that updating workshop content in a live session in this way isn't going to undo any deployments or changes you make in the Kubernetes cluster for that session. So if wanting to retest parts of the workshop instructions you may have to manually undo changes in the cluster in order to replay them. This will depend on your specific workshop content.

Custom workshop image changes
-----------------------------

If your workshop is using a custom workshop image because of the need to provide additional tools, and you have as a result also included the workshop instructions as part of the workshop image, during development of workshop content always use an image tag of ``main``, ``master``, ``develop`` or ``latest``, do not use a version image reference.

```
apiVersion: training.eduk8s.io/v1alpha2
kind: Workshop
metadata:
  name: lab-sample-workshop
spec:
  title: Sample Workshop
  description: A sample workshop
  content:
    image: ghcr.io/vmware-tanzu-labs/lab-sample-workshop:master
```

When an image tag of ``main``, ``master``, ``develop`` or ``latest`` is used, the image pull policy will be set to ``Always`` ensuring that the custom workshop image will be pulled down again for a new workshop session if the remote image had changed. If the image tag was for a specific version, it would be necessary to change the workshop definition every time there was a change to the workshop image.

Custom workshop image overlay
-----------------------------

Even where you have a custom workshop image, setup the workshop definition to also pull down the workshop content from the hosted Git repository or web server.

```
apiVersion: training.eduk8s.io/v1alpha2
kind: Workshop
metadata:
  name: lab-sample-workshop
spec:
  title: Sample Workshop
  description: A sample workshop
  content:
    image: ghcr.io/vmware-tanzu-labs/lab-sample-workshop:master
    files: github.com/vmware-tanzu-labs/lab-sample-workshop
```

By pulling down the workshop content as an overlay when the workshop session started, on top of the contents of the custom workshop image, you only need to rebuild the custom workshop image when needing to make changes to what additional tools are needed, or when you want to ensure the latest workshop instructions are also a part of the final custom workshop image.

Using this method, as the location of the workshop files is known you can then also do live updates of workshop content in the session as described previously.

If the additional set of tools required for a workshop is not too specific to a workshop, it is recommended to create a standalone workshop base image where just the tools are added. Content for a specific workshop would then always be pulled down from a Git repository or web server when the workshop session is started.

```
apiVersion: training.eduk8s.io/v1alpha2
kind: Workshop
metadata:
  name: lab-sample-workshop
spec:
  title: Sample Workshop
  description: A sample workshop
  content:
    image: ghcr.io/vmware-tanzu-labs/custom-environment:master
    files: github.com/vmware-tanzu-labs/lab-sample-workshop
```

This separates generic tooling from specific workshops and allows the custom workshop base image to be used for multiple workshops on different, but related topics, which require the same tooling.

Changes to workshop defintion
-----------------------------

By default, if you need to modify the definition for a workshop, you would need to delete the training portal instance, update the workshop definition in the cluster, and recreate the training portal.

During development of workshop content, when working on the workshop definition itself to change things like resource allocations, role access, or what resource objects are automatically created for the workshop environment or a specific workshop session, you can in the training portal definition enable automatic updates on changes to the workshop definition.

```
apiVersion: training.eduk8s.io/v1alpha1
kind: TrainingPortal
metadata:
  name: lab-sample-workshop
spec:
  portal:
    sessions:
      maximum: 1
    updates:
      workshop: true
  workshops:
  - name: lab-sample-workshop
    expires: 120m
    orphaned: 15m
```

With this option enabled, whenever the workshop definition in the cluster is modified, the existing workshop environment managed by the training portal for that workshop, will be shutdown and replaced with a new workshop environment using the updated workshop definition.

In the case there is still an active workshop session running, the actual deletion of the old workshop environment will be delayed until that workshop session is terminated.

Local build of workshop image
-----------------------------

Even if not packaging up a workshop into a custom workshop image, for local development of workshop content using a Kubernetes cluster on your own machine, to avoid the need to keep pushing changes up to a hosted Git repository, it can be easier to build a custom workshop image locally on your own machine using ``docker``.

In order to do this, and avoid having to still push the image to a public image registry on the internet, you will need to deploy an image registry to your local Kubernetes cluster where Educates is being run. For a basic deployment of an image registry in a local cluster access would usually be insecure. This will mean that you have to configure the Kubernetes cluster to trust the insecure registry. This may be difficult to do depending on the Kubernetes cluster being used, but makes for quicker turnaround as you will not have to push or pull the custom workshop image across the public internet.

Once the custom workshop image built locally has been pushed to the local image registry, the image reference in the workshop definition can be set to pull it from the local registry in the same cluster. To ensure that the custom workshop image is always pulled for a new workshop session if updated, use the ``latest`` tag when tagging and pushing the image to the local registry.
