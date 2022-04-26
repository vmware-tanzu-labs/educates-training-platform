Local Environment
=================

For local development of workshop content the Educates project provides a package for creating a local Kubernetes cluster using Kind, running Educates. This includes an image registry for storing workshop content files and custom workshop base images. The out of the box configuration for the local environment uses a `nip.io` address for access, but it can be configured to use a custom ingress domain and corresponding TLS certficate.

Deleting the cluster
--------------------

If you are done with the local environment and want to delete the Kubernetes cluster, run:

```
educates-local-dev/delete-cluster.sh
```

You can then run `create-cluster.sh` to recreate the Kubernetes cluster.

If you know you do not intend to recreate the Kubernetes cluster, and so want everything deleted, you will also need to separately delete the DNS resolver if deployed.

Reinstalling Educates
---------------------

When you run the `create-cluster.sh` script to create the local Kubernetes cluster, it will also install Educates. If you wish to delete and reinstall Educates after the cluster has been created, first run:

```
educates-local-dev/delete-educates.sh
```

To deploy Educates again, you can then run:

```
educates-local-dev/deploy-educates.sh
```

Local image registry
--------------------

When you run the `create-cluster.sh` script to create the local Kubernetes cluster, it will also install an image registry into the Kubernetes cluster. This is used for storing workshop content files and custom workshop base images.

The `Makefile` supplied with the new workshop provides targets for `make` to build and publish both workshop content files and a custom workshop base image. If you want to use the registry to store other images, you should tag your images with the registry host/port of `localhost:5001`, then push the image to the registry. If you want to pull images from the registry in deployments created in the Kubernetes cluster, you should use the registry host/port of `registry.default.svc.cluster.local:5001` in the deployment resources created inside of the Kubernetes cluster.

So that the same host name is used on the local machine as in the cluster, you could if you want create an entry in the `/etc/hosts` file of you local machine for `registry.default.svc.cluster.local` which maps to `127.0.0.1`.

If you wish to delete and reinstall the registry after the cluster has been created, you can run:

```
educates-local-dev/delete-registry.sh
```

To deploy the registry again, you can then run:

```
educates-local-dev/deploy-registry.sh
```

Custom ingress domain
---------------------

By default when deployed to the Kubernetes cluster of the local environment, Educates will be configured to use a `nip.io` address for the ingress domain, as a wildcard domain.

This works but because it is not possible to obtain a TLS certificate for a `nip.io` address, and as such it is not possible to use secure ingresses, some features of the workshop environment will not work. This includes the inability to use a per session image registry, which requires a secure ingress to be trusted by the Kubernetes cluster and other tools which work with registries.

Instead of relying on a `nip.io` address you have two options:

* Use your own domain that you control and for which you can generate yourself a wildcard TLS certificate. For example, you might own the domain `workshops.mydomain.com`, in which case you would also need a wildcard TLS certificate for `*.workshops.mydomain.com`. You will also need to be able to configure DNS for the domain, or be able to set up a local DNS resolver on your local machine.

* Use the `educates-local-dev.xyz` domain. This will require that you obtain a copy of a wildcard TLS certificate for that domain from the Educates team. You will also need to be able to set up a local DNS resolver on your local machine.

To use a custom ingress domain, before the local Kubernetes cluster is created using the `cluster-create.sh` script, create the file:

```
educates-local-dev/local-settings.env
```

and in the file add a setting for `INGRESS_DOMAIN`. For example:

```
INGRESS_DOMAIN=educates-local-dev.xyz
```

If you have the wildcard TLS certificate for the ingress domain, you need to create a file with name of form:

```
educates-local-dev/${INGRESS_DOMAIN}-tls.yaml
```

That is, a file with name matching the ingress domain, with `-tls.yaml` extension.

The contents of the file should be a Kubernetes secret of type `tls` created from the TLS wildcard certificate. The name of the secret resource should be of form `${INGRESS_DOMAIN}-tls`, matching the ingress domain with `-tls` suffix.

If you had used certbot to create the wildcard TLS certificate using a DNS challenge, you would create the Kubernetes secret by running:

```
kubectl create secret tls ${INGRESS_DOMAIN}-tls \
 --cert=$HOME/.letsencrypt/config/live/${INGRESS_DOMAIN}/fullchain.pem \
 --key=$HOME/.letsencrypt/config/live/${INGRESS_DOMAIN}/privkey.pem \
 --dry-run=client -o yaml > educates-local-dev/${INGRESS_DOMAIN}-tls.yaml
 ```

Now when Educates is deployed using `cluster-create.sh`, or later if using `deploy-educates.sh` to reinstall Educates, this custom ingress domain and wildcard TLS certificate will be used.

Note that DNS still needs to be configured to map using a CNAME the wildcard domain to the IP address of your local host machine where the Kubernetes cluster is running. This could be done by modifying your actual DNS registry, or you can run a local DNS resolver. If doing this in your global DNS registry, it doesn't matter that the IP address is a local network address which is not accessible to the internet, although depending on what internet router you use for a home network, you may need to disable DNS rebinding protection in your router for the domain.

Local DNS resolver
------------------

The alternative to setting up a global DNS registry to map the wildcard domain to the IP address of your local host machine, is to run a local DNS resolver for the ingress domain. This requires being able to run `dnsmasq` or equivalent locally and configuring the local DNS resolution to forward lookups for the ingress domain to the local DNS resolver.

If you are on macOS, a script is provided to run `dnsmasq` for you with the required configuration. To start this run:

```
educates-local-dev/deploy-resolver.sh
```

This will run the `dnsmasq` instance in the local docker daemon instance.

Next ensure that the directory `/etc/resolver` exists:

```
sudo mkdir /etc/resolver
```

In that directory create a file with name the same as the ingress domain, with `nameserver` entry pointing at `127.0.0.1`.

```
sudo cat > /etc/resolver/${INGRESS_DOMAIN} << EOF
nameserver 127.0.0.1
EOF
```

To test that the DNS resolver is working correctly run:

```
scutil --dns www.${INGRESS_DOMAIN}
```

You should see an entry like the following for your ingress domain:

```
resolver #8
  domain   : educates-local.dev.xyz
  nameserver[0] : 127.0.0.1
  flags    : Request A records, Request AAAA records
  reach    : 0x00030002 (Reachable,Local Address,Directly Reachable Address)
```

Note that tools like `nslookup` and `dig` do not use the local DNS resolver so don't expect them to show a result. You can instead use `curl` to test a host within the ingress domain. You should get a HTTP 404 response, which will be the default response from the Kubernetes ingress controller, since there will not be any ingress configured to respond to the request.

```
$ curl -v www.educates-local.dev.xyz
*   Trying 192.168.168.1:80...
* Connected to www.educates-local.dev.xyz (192.168.168.1) port 80 (#0)
> GET / HTTP/1.1
> Host: www.educates-local.dev.xyz
> User-Agent: curl/7.79.1
> Accept: */*
> 
* Mark bundle as not supporting multiuse
< HTTP/1.1 404 Not Found
< vary: Accept-Encoding
< date: Fri, 25 Mar 2022 03:07:19 GMT
< server: envoy
< content-length: 0
< 
* Connection #0 to host www.educates-local.dev.xyz left intact
```

Linux systems have their own ways of setting up a local DNS resolver and how that is done will depend on the Linux distributions. This generally requires disabling DNS handling by `systemd` and instead enabling DNS handling using `dnsmasq`. The `dnsmasq` server should then be configured with an entry like the following:

```
address=/educates-local.dev.xyz/192.168.168.1
```

where your ingress domain is mapped to the IP address of your local machine.

When done with the local environment and you want to delete the local DNS resolver if started on macOS, you can run:

```
educates-local-dev/delete-resolver.sh
```

You will need to manually remove the file you created under `/etc/resolver`.