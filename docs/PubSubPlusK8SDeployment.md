# Solace PubSub+ Software Event Broker on Kubernetes Deployment Documentation

This document provides detailed information for deploying Solace PubSub+ Software Event Broker on Kubernetes.

* For a hands-on quick start, refer to the [Quick Start guide](/README.md).
* For the `pubsubplus` Helm chart configuration options, refer to the [PubSub+ Software Event Broker Helm Chart Reference](/pubsubplus/README.md).

This document is applicable to any platform provider supporting Kubernetes.

Contents:
  * [**The Solace PubSub+ Software Event Broker**](#the-solace-pubsub-software-event-broker)
  * [**Overview**](#overview)
  * [**PubSub+ Event Broker Deployment Considerations**](#pubsub-software-event-broker-deployment-considerations)
    + [Deployment scaling](#deployment-scaling)
      - [Simplified vertical scaling](#simplified-vertical-scaling)
      - [Comprehensive vertical scaling](#comprehensive-vertical-scaling)
      - [Enabling a Disruption Budget for HA deployment](#enabling-a-disruption-budget-for-ha-deployment)
      - [Reducing resource requirements of Monitoring Nodes in an HA deployment](#reducing-resource-requirements-of-monitoring-nodes-in-an-ha-deployment)
    + [Disk Storage](#disk-storage)
      - [Allocating smaller storage to Monitor pods in an HA deployment](#allocating-smaller-storage-to-monitor-pods-in-an-ha-deployment)
      - [Using the default or an existing storage class](#using-the-default-or-an-existing-storage-class)
      - [Creating a new storage class](#creating-a-new-storage-class)
      - [Using an existing PVC (Persistent Volume Claim)](#using-an-existing-pvc-persistent-volume-claim-)
      - [Using a pre-created provider-specific volume](#using-a-pre-created-provider-specific-volume)
      - [Tested storage environments and providers](#tested-storage-environments-and-providers)
    + [Exposing the PubSub+ Event Broker Services](#exposing-the-pubsub-software-event-broker-services)
      - [Specifying Service Type](#specifying-service-type)
      - [Using Ingress to access event broker services](#using-ingress-to-access-event-broker-services)
        * [Configuration examples](#configuration-examples)
        * [HTTP, no TLS](#http-no-tls)
        * [HTTPS with TLS terminate at ingress](#https-with-tls-terminate-at-ingress)
        * [HTTPS with TLS re-encrypt at ingress](#https-with-tls-re-encrypt-at-ingress)
        * [General TCP over TLS with passthrough to broker](#general-tcp-over-tls-with-passthrough-to-broker)
      - [Using pod label "active" to identify the active event broker node](#using-pod-label-active-to-identify-the-active-event-broker-node)
    + [Enabling use of TLS to access broker services](#enabling-use-of-tls-to-access-broker-services)
      - [Setting up TLS](#setting-up-tls)
      - [Rotating the server key](#rotating-the-server-key)
    + [The PubSub+ Docker image](#the-pubsub-software-event-broker-docker-image)
      - [Using a public registry](#using-a-public-registry)
      - [Using private registries](#using-private-registries)
      - [Using ImagePullSecrets for signed images](#using-imagepullsecrets-for-signed-images)
    + [Security considerations](#security-considerations)
      - [Using Security Context](#using-security-context)
      - [Enabling pod label "active" in a tight security environment](#enabling-pod-label-active-in-a-tight-security-environment)
    + [User management considerations](#user-management-considerations)
      - [Adding new users](#adding-new-users)
      - [Changing user passwords](#changing-user-passwords)
  * [**Deployment Prerequisites**](#deployment-prerequisites)
    + [Platform and tools setup](#platform-and-tools-setup)
      - [Install the `kubectl` command-line tool](#install-the-kubectl-command-line-tool)
      - [Perform any necessary Kubernetes platform-specific setup](#perform-any-necessary-kubernetes-platform-specific-setup)
      - [Install and setup the Helm package manager](#install-and-setup-the-helm-package-manager)
  * [**Deployment steps**](#deployment-steps)
    + [Deployment steps using Helm](#deployment-steps-using-helm)
    + [Alternative Deployment with generating templates for the Kubernetes `kubectl` tool](#alternative-deployment-with-generating-templates-for-the-kubernetes-kubectl-tool)
  * [**Validating the Deployment**](#validating-the-deployment)
    + [Gaining admin access to the event broker](#gaining-admin-access-to-the-event-broker)
      - [Admin Password](#admin-password)
      - [WebUI, SolAdmin and SEMP access](#webui-soladmin-and-semp-access)
      - [Solace CLI access](#solace-cli-access)
      - [SSH access to individual event brokers](#ssh-access-to-individual-event-brokers)
    + [Testing data access to the event broker](#testing-data-access-to-the-event-broker)
  * [**Troubleshooting**](#troubleshooting)
    + [Viewing logs](#viewing-logs)
    + [Viewing events](#viewing-events)
    + [PubSub+ Software Event Broker troubleshooting](#pubsub-software-event-broker-troubleshooting)
      - [General Kubernetes troubleshooting hints](#general-kubernetes-troubleshooting-hints)
      - [Pods stuck in not enough resources](#pods-stuck-in-not-enough-resources)
      - [Pods stuck in no storage](#pods-stuck-in-no-storage)
      - [Pods stuck in CrashLoopBackoff, Failed or Not Ready](#pods-stuck-in-crashloopbackoff-failed-or-not-ready)
      - [No Pods listed](#no-pods-listed)
      - [Security constraints](#security-constraints)
  * [**Modifying or upgrading a Deployment**](#modifying-or-upgrading-a-deployment)
      - [Upgrade example](#upgrade-example)
      - [Modification example](#modification-example)
  * [**Re-installing a Deployment**](#re-installing-a-deployment)
  * [**Deleting a Deployment**](#deleting-a-deployment)
  * [**Backing Up and Restore**](#backing-up-and-restore)



## The Solace PubSub+ Software Event Broker

The [PubSub+ Software Event Broker](https://solace.com/products/event-broker/) of the [Solace PubSub+ Platform](https://solace.com/products/platform/) efficiently streams event-driven information between applications, IoT devices and user interfaces running in the cloud, on-premises, and hybrid environments using open APIs and protocols like AMQP, JMS, MQTT, REST and WebSocket. It can be installed into a variety of public and private clouds, PaaS, and on-premises environments, and brokers in multiple locations can be linked together in an [event mesh](https://solace.com/what-is-an-event-mesh/) to dynamically share events across the distributed enterprise.

## Overview

This document assumes a basic understanding of [Kubernetes concepts](https://kubernetes.io/docs/concepts/).

For an example deployment diagram, check out the [PubSub+ Event Broker on Google Kubernetes Engine (GKE) quickstart](https://github.com/SolaceProducts/pubsubplus-gke-quickstart#how-to-deploy-solace-pubsub-software-event-broker-onto-gke).

Multiple YAML templates define the PubSub+ Kubernetes deployment with several parameters as deployment options. The templates are packaged as the `pubsubplus` [Helm chart](//helm.sh/docs/topics/charts/) to enable easy customization by only specifying the non-default parameter values, without the need to edit the template files.

There are two deployment options described in this document:
* The recommended option is to use the [Kubernetes Helm tool](https://github.com/helm/helm/blob/master/README.md), which can also manage your deployment's lifecycle, including upgrade and delete.
* Another option is to generate a set of templates with customized values from the PubSub+ Helm chart and then use the Kubernetes native `kubectl` tool to deploy. The deployment will use the authorizations of the requesting user. However, in this case, Helm will not be able to manage your Kubernetes rollouts lifecycle.

It is also important to know that Helm is a templating tool that helps package PubSub+ Software Event Broker deployment into charts.
It is most useful when first setting up broker nodes on the Kubernetes cluster. It can handle the install-update-delete lifecycle for the broker nodes deployed to the cluster.
It can not be used to scale-up, scale down or apply custom configuration to an already deployed PubSub+ Software Event Broker.

The next sections will provide details on the PubSub+ Helm chart, dependencies and customization options, followed by [deployment prerequisites](#deployment-prerequisites) and the actual [deployment steps](#deployment-steps).

## PubSub+ Software Event Broker Deployment Considerations

The following diagram illustrates the template organization used for the PubSub+ Deployment chart. Note that the minimum is shown in this diagram to give you some background regarding the relationships and major functions.
![alt text](/docs/images/template_relationship.png "`pubsubplus` chart template relationship")

The StatefulSet template controls the pods of a PubSub+ Software Event Broker deployment. It also mounts the scripts from the ConfigMap and the files from the Secrets and maps the event broker data directories to a storage volume through a StorageClass, if configured. The Service template provides the event broker services at defined ports. The Service-Discovery template is only used internally, so pods in a PubSub+ event broker redundancy group can communicate with each other in an HA setting.

All the `pubsubplus` chart parameters are documented in the [PubSub+ Software Event Broker Helm Chart](/pubsubplus/README.md#configuration) reference.

### Deployment scaling

Solace PubSub+ Software Event Broker can be scaled vertically by specifying either:
* `solace.size` - simplified scaling along the maximum number of client connections; or
* `solace.systemScaling` - enables defining all scaling parameters and pod resources

Depending on the `solace.redundancy` parameter, one event router pod is deployed in a single-node standalone deployment or three pods if deploying a [High-Availability (HA) group](//docs.solace.com/Overviews/SW-Broker-Redundancy-and-Fault-Tolerance.htm).

Horizontal scaling is possible through [connecting multiple deployments](//docs.solace.com/Overviews/DMR-Overview.htm).

#### Simplified vertical scaling

The broker nodes are scaled by the [maximum number of concurrent client connections](//docs.solace.com/Configuring-and-Managing/SW-Broker-Specific-Config/System-Scaling-Parameters.htm#max-client-connections), controlled by the `solace.size` chart parameter.

The broker container CPU and memory resource requirements are assigned according to the tier, and are summarized here from the [Solace documentation](//docs.solace.com/Configuring-and-Managing/SW-Broker-Specific-Config/System-Resource-Requirements.htm#res-req-container) for the possible `solace.size` parameter values:
* `dev`: no guaranteed performance, minimum requirements: 1 CPU, 3.4 GiB memory
* `prod100`: up to 100 connections, minimum requirements: 2 CPU, 3.4 GiB memory
* `prod1k`: up to 1,000 connections, minimum requirements: 2 CPU, 6.4 GiB memory
* `prod10k`: up to 10,000 connections, minimum requirements: 4 CPU, 12.2 GiB memory
* `prod100k`: up to 100,000 connections, minimum requirements: 8 CPU, 30.3 GiB memory
* `prod200k`: up to 200,000 connections, minimum requirements: 12 CPU, 51.4 GiB memory

#### Comprehensive vertical scaling

This option overrides simplified vertical scaling. It enables specifying each supported broker scaling parameter, currently:
* "maxConnections", in `solace.systemScaling.maxConnections` parameter
* "maxQueueMessages", in `solace.systemScaling.maxQueueMessages` parameter
* "maxSpoolUsage", in `solace.systemScaling.maxSpoolUsage` parameter

Additionally, CPU and memory must be sized and provided in `solace.systemScaling.cpu` and `solace.systemScaling.memory` parameters. Use the [Solace online System Resource Calculator](https://docs.solace.com/Configuring-and-Managing/SW-Broker-Specific-Config/System-Resource-Calculator.htm) to determine CPU and memory requirements for the selected scaling parameters.

Note: beyond CPU and memory requirements, required storage size (see next section) also depends significantly on scaling. The calculator can be used to determine that as well.

Also note, that specifying maxConnections, maxQueueMessages and maxSpoolUsage on initial deployment will overwrite the broker’s default values. On the other hand, doing the same using Helm upgrade on an existing deployment will not overwrite these values on brokers configuration, but it can be used to prepare (first step) for a manual scale up through CLI where these parameters can be actually changed (second step).

#### Enabling a Disruption Budget for HA deployment

One of the important parameters available to configure PubSub+ Software Event Broker HA is the [`podDisruptionBudget`](https://kubernetes.io/docs/tasks/run-application/configure-pdb/).
This helps you control and limit the disruption to your application when its pods need to be rescheduled for upgrades, maintenance or any other reason.
This is only available when we have the PubSub+ Software Event Broker deployed in [high-availability (HA) mode](//docs.solace.com/Overviews/SW-Broker-Redundancy-and-Fault-Tolerance.htm), that is, `solace.redundancy=true`.

In an HA deployment with Primary, Backup and Monitor nodes, we require a minimum of 2 nodes to reach a quorum. The pod disruption budget defaults to a minimum of two nodes when enabled.

To enable this functionality you have to set  `solace.podDisruptionBudgetForHA=true` and `solace.redundancy=true`.


#### Reducing resource requirements of Monitoring Nodes in an HA deployment

The Kubernetes StatefulSet which controls the pods that make up a PubSub+ broker [deployment in an HA redundancy group](#deployment-scaling) does not distinguish between PubSub+ HA node types: it assigns the same CPU and memory resources to pods hosting worker and monitoring node types, even though monitoring nodes have minimal resource requirements.

To address this, a "solace-pod-modifier" Kubernetes admission plugin is provided as part of this repo: when deployed it intercepts pod create requests and can set the lower resource requirements for broker monitoring nodes only.

Also ensure to define the Helm chart parameter `solace.podModifierEnabled: true` to provide the necessary annotations to the PubSub+ broker pods, which acts as a "control switch" to enable the monitoring pod resource modification.

Refer to the [Readme of the plugin](/solace-pod-modifier-admission-plugin/README.md) for details on how to activate and use it. Note: the plugin requires Kubernetes v1.16 or later.

> Note: the use of the "solace-pod-modifier" Kubernetes admission plugin is not mandatory. If it is not activated or not working then the default behavior applies: monitoring nodes will have the same resource requirements as the worker nodes. If "solace-pod-modifier" is activated later, then as long as the monitoring node pods have the correct annotations they can be deleted and the reduced resources will apply after they are recreated .

### Disk Storage

The [PubSub+ deployment uses disk storage](//docs.solace.com/Configuring-and-Managing/Configuring-Storage.htm#Storage-) for logging, configuration, guaranteed messaging and other purposes, allocated from Kubernetes volumes.

Broker versions prior to 9.12 required separate volumes mounted for each storage functionality, making up a [storage-group from individual storage-elements](https://docs.solace.com/Configuring-and-Managing/SW-Broker-Specific-Config/Configuring-Storage.htm). Versions 9.12 and later can have a single mount storage-group that will be divided up internally, but they still support the legacy mounting of storage-elements. It is recommended to set the parameter `storage.useStorageGroup=true` if using broker version 9.12 or later - do not use it on earlier versions.

If using [simplified vertical scaling](#simplified-vertical-scaling), set following storage size (`storage.size` parameter) for the scaling tiers:
* `dev`: no guaranteed performance: 5GB
* `prod100`: up to 100 connections, 7GB
* `prod1k`: up to 1,000 connections, 14GB
* `prod10k`: up to 10,000 connections, 18GB
* `prod100k`: up to 100,000 connections, 30GB
* `prod200k`: up to 200,000 connections, 34GB

If using [Comprehensive vertical scaling](#comprehensive-vertical-scaling), use the [calculator](https://docs.solace.com/Configuring-and-Managing/SW-Broker-Specific-Config/System-Resource-Calculator.htm) to determine storage size.

Using a persistent storage is recommended, otherwise if pod-local storage is used data will be lost with the loss of a pod. The `storage.persistent` parameter is set to `true` by default.

The `pubsubplus` chart supports allocation of new storage volumes or mounting volumes with existing data. To avoid data corruption ensure to allocate clean new volumes for new deployments.

The recommended default allocation is to use Kubernetes [Storage Classes](//kubernetes.io/docs/concepts/storage/storage-classes/) utilizing [Dynamic Volume Provisioning](//kubernetes.io/docs/concepts/storage/dynamic-provisioning/). The `pubsubplus` chart deployment will create a Persistent Volume Claim (PVC) specifying the size and the Storage Class of the requested volume and a Persistent Volume (PV) that meets the requirements will be allocated. Both the PVC and PV names will be linked to the deployment's name. When deleting the event broker pod(s) or even the entire deployment, the PVC and the allocated PV will not be deleted, so potentially complex configuration is preserved. They will be re-mounted and reused with the existing configuration when a new pod starts (controlled by the StatefulSet, automatically matched to the old pod even in an HA deployment) or deployment with the same as the old name is started. Explicitly delete a PVC if no longer needed, which will delete the corresponding PV - refer to [Deleting a Deployment](#deleting-a-deployment).

Instead of using a storage class, the `pubsubplus` chart also allows you describe how to assign storage by adding your own YAML fragment in the `storage.customVolumeMount` parameter. The fragment is inserted for the `data` volume in the `{spec.template.spec.volumes}` section of the ConfigMap. Note that in this case the `storage.useStorageClass` parameter is ignored.

Followings are examples of how to specify parameter values in common use cases:

#### Allocating smaller storage to Monitor pods in an HA deployment

When deploying PubSub+ in an HA redundancy group, monitoring nodes have minimal storage requirements compared to working nodes. The default `storage.monitorStorageSize` Helm chart value enables setting and creating smaller storage for Monitor pods hosting monitoring nodes as a pre-install hook in an HA deployment (`solace.redundancy=true`), before larger storage would be automatically created. Note that this setting is effective for initial deployments only, cannot be used to upgrade an existing deployment with storage already allocated for monitoring nodes. A workaround is to mark the Monitor pod storage for delete (will not delete it immediately, only after the Monitor pod has been deleted) then follow the steps to [recreate the deployment](#re-installing-a-deployment): `kubectl delete pvc <monitoring-pod-pvc>`.

#### Using the default or an existing storage class

Set the `storage.useStorageClass` parameter to use a particular storage class or leave this parameter to default undefined to allocate from your platform's "default" storage class - ensure it exists.
```bash
# Check existing storage classes
kubectl get storageclass
```

#### Creating a new storage class

Create a [specific storage class](//kubernetes.io/docs/concepts/storage/storage-classes/#provisioner) if no existing storage class meets your needs. Refer to your Kubernetes environment's documentation if a StorageClass needs to be created or to understand the differences if there are multiple options. Example:
```yaml
# AWS fast storage class example
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: fast
provisioner: kubernetes.io/aws-ebs
parameters:
  type: io1
  fsType: xsf
```

If using NFS, or generally if allocating from a defined Kubernetes [Persistent Volume](//kubernetes.io/docs/concepts/storage/persistent-volumes/#persistent-volumes), specify a `storageClassName` in the PV manifest as in this NFS example, then set the `storage.useStorageClass` parameter to the same:
```yaml
# Persistent Volume example
apiVersion: v1
kind: PersistentVolume
metadata:
  name: pv0003
spec:
  storageClassName: nfs
  capacity:
    storage: 5Gi
  volumeMode: Filesystem
  accessModes:
    - ReadWriteOnce
  persistentVolumeReclaimPolicy: Recycle
  mountOptions:
    - hard
    - nfsvers=4.1
  nfs:
    path: /tmp
    server: 172.17.0.2
```
> Note: NFS is currently supported for development and demo purposes. If using NFS also set the `storage.slow` parameter to 'true'.
<br/>

#### Using an existing PVC (Persistent Volume Claim)

You can to use an existing PVC with its associated PV for storage, but it must be taken into account that the deployment will try to use any existing, potentially incompatible, configuration data on that volume.

Provide this custom YAML fragment in `storage.customVolumeMount`:

```yaml
  customVolumeMount: |
    persistentVolumeClaim:
      claimName: existing-pvc-name
```

#### Using a pre-created provider-specific volume

The PubSub+ Software Event Broker Kubernetes deployment is expected to work with all [types of volumes](//kubernetes.io/docs/concepts/storage/volumes/#types-of-volumes ) your environment supports. In this case provide the specifics on mounting it in a custom YAML fragment in `storage.customVolumeMount`.

The following shows how to implement the [gcePersistentDisk example](//kubernetes.io/docs/concepts/storage/volumes/#gcepersistentdisk); note how the portion of the pod manifest example after `{spec.volumes.name}` is specified:
```yaml
  customVolumeMount: |
    gcePersistentDisk:
      pdName: my-data-disk
      fsType: ext4
```
<br/>

Another example is using [hostPath](//kubernetes.io/docs/concepts/storage/volumes/#hostpath):
```yaml
  customVolumeMount: |
    hostPath:
      # directory location on host
      path: /data
      # this field is optional
      type: Directory
```
#### Tested storage environments and providers

The PubSub+ Software Event Broker has been tested to work with the following, Portworx, Ceph, Cinder (Openstack), vSphere storage for Kubernetes as documented [here](https://docs.solace.com/Cloud/Deployment-Considerations/resource-requirements-k8s.htm#supported-storage-solutions).
However, note that for [EKS](https://docs.solace.com/Cloud/Deployment-Considerations/installing-ps-cloud-k8s-eks-specific-req.htm) and [GKE](https://docs.solace.com/Cloud/Deployment-Considerations/installing-ps-cloud-k8s-gke-specific-req.htm#storage-class), `xfs` produced the best results during tests.
[AKS](https://docs.solace.com/Cloud/Deployment-Considerations/installing-ps-cloud-k8s-aks-specific-req.htm) users can opt for `Local Redundant Storage (LRS)` redundancy. This is because they produce the best results
when compared with the other types available on Azure.

### Exposing the PubSub+ Software Event Broker Services

#### Specifying Service Type

[PubSub+ services](//docs.solace.com/Configuring-and-Managing/Default-Port-Numbers.htm#Software) can be exposed through one of the following [Kubernetes service types](//kubernetes.io/docs/concepts/services-networking/service/#publishing-services-service-types) by specifying the `service.type` parameter:

* LoadBalancer (default) - a load balancer, typically externally accessible depending on the K8s provider.
* NodePort - maps PubSub+ services to a port on a Kubernetes node; external access depends on access to the node.
* ClusterIP - internal access only from within K8s.

Additionally, for all above service types, external access can be configured through K8s Ingress (see next section).

To support [Internal load balancers](//kubernetes.io/docs/concepts/services-networking/service/#internal-load-balancer), provider-specific service annotation may be added through defining the `service.annotations` parameter.

The `service.ports` parameter defines the services exposed. It specifies the event broker `containerPort` that provides the service and the mapping to the `servicePort` where the service can be accessed when using LoadBalancer or ClusterIP. Note that there is no control over which port services are mapped when using NodePort.

When using Helm to initiate a deployment, notes will be provided on the screen about how to obtain the service addresses and ports specific to your deployment - follow the "Services access" section of the notes. 

A deployment is ready for service requests when there is a Solace pod that is running, `1/1` ready, and the pod's label is "active=true." The exposed `pubsubplus` service will forward traffic to that active event broker node. **Important**: service means here [Guaranteed Messaging level of  Quality-of-Service (QoS) of event messages persistence](//docs.solace.com/PubSub-Basics/Guaranteed-Messages.htm). Messaging traffic will not be forwarded if service level is degraded to [Direct Messages](//docs.solace.com/PubSub-Basics/Direct-Messages.htm) only.

#### Using Ingress to access event broker services

The `LoadBalancer` or `NodePort` service types can be used to expose all services from one PubSub+ broker. [Ingress](https://kubernetes.io/docs/concepts/services-networking/ingress) may be used to enable efficient external access from a single external IP address to specific PubSub+ services, potentially provided by multiple brokers.

The following table gives an overview of how external access can be configured for PubSub+ services via Ingress.

| PubSub+ service / protocol, configuration and requirements | HTTP, no TLS | HTTPS with TLS terminate at ingress | HTTPS with TLS re-encrypt at ingress | General TCP over TLS with passthrough to broker |
| -- | -- | -- | -- | -- |
| **Notes:** | -- | Requires TLS config on Ingress-controller | Requires TLS config on broker AND TLS config on Ingress-controller | Requires TLS config on broker. Client must use SNI to provide target host |
| WebSockets, MQTT over WebSockets | Supported | Supported | Supported | Supported (routing via SNI) |
| REST | Supported with restrictions: if publishing to a Queue, only root path is supported in Ingress rule or must use [rewrite target](https://github.com/kubernetes/ingress-nginx/blob/main/docs/examples/rewrite/README.md) annotation. For Topics, the initial path would make it to the topic name. | Supported, see prev. note | Supported, see prev. note | Supported (routing via SNI) |
| SEMP | Not recommended to expose management services without TLS | Supported with restrictions: (1) Only root path is supported in Ingress rule or must use [rewrite target](https://github.com/kubernetes/ingress-nginx/blob/main/docs/examples/rewrite/README.md) annotation; (2) Non-TLS access to SEMP [must be enabled](https://docs.solace.com/Configuring-and-Managing/configure-TLS-broker-manager.htm) on broker | Supported with restrictions: only root path is supported in Ingress rule or must use [rewrite target](https://github.com/kubernetes/ingress-nginx/blob/main/docs/examples/rewrite/README.md) annotation | Supported (routing via SNI) |
| SMF, SMF compressed, AMQP, MQTT | - | - | - | Supported (routing via SNI) |
| SSH* | - | - | - | - |

*SSH has been listed here for completeness only, external exposure not recommended.

##### Configuration examples

All examples assume NGINX used as ingress controller ([documented here](https://kubernetes.github.io/ingress-nginx/)), selected because NGINX is supported by most K8s providers. For [other ingress controllers](https://kubernetes.io/docs/concepts/services-networking/ingress-controllers/#additional-controllers) refer to their respective documentation.

To deploy the NGINX Ingress Controller, refer to the [Quick start in the NGINX documentation](https://kubernetes.github.io/ingress-nginx/deploy/#quick-start). After successful deployment get the ingress External-IP or FQDN with the following command:

`kubectl get service ingress-nginx-controller --namespace=ingress-nginx`

This is the IP (or the IP address the FQDN resolves to) of the ingress where external clients shall target their request and any additional DNS-resolvable hostnames, used for name-based virtual host routing, must also be configured to resolve to this IP address. If using TLS then the host certificate Common Name (CN) and/or Subject Alternative Name (SAN) must be configured to match the respective FQDN.

For options to expose multiple services from potentially multiple brokers, review the [Types of Ingress from the Kubernetes documentation](https://kubernetes.io/docs/concepts/services-networking/ingress/#types-of-ingress).
 
The next examples provide Ingress manifests that can be applied using `kubectl apply -f <manifest-yaml>`. Then check that an external IP address (ingress controller external IP) has been assigned to the rule/service and also that the host/external IP is ready for use as it could take a some time for the address to be populated.

```
kubectl get ingress
NAME                              CLASS   HOSTS
ADDRESS         PORTS   AGE
example.address                   nginx   frontend.host
20.120.69.200   80      43m
```

##### HTTP, no TLS

The following example configures ingress to [access PubSub+ REST service](https://docs.solace.com/RESTMessagingPrtl/Solace-REST-Example.htm#cURL). Replace `<my-pubsubplus-service>` with the name of the service of your deployment (hint: the service name is similar to your pod names). The port name must match the `service.ports` name in the PubSub+ `values.yaml` file.

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: http-plaintext-example
spec:
  ingressClassName: nginx
  rules:
  - http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: <my-pubsubplus-service>
            port:
              name: tcp-rest
```

External requests shall be targeted to the ingress External-IP at the HTTP port (80) and the specified path.

##### HTTPS with TLS terminate at ingress

Additional to above, this requires specifying a target virtual DNS-resolvable host (here `https-example.foo.com`), which resolves to the ingress External-IP, and a `tls` section. The `tls` section provides the possible hosts and corresponding [TLS secret](https://kubernetes.io/docs/concepts/services-networking/ingress/#tls) that includes a private key and a certificate. The certificate must include the virtual host FQDN in its CN and/or SAN, as described above. Hint: [TLS secrets can be easily created from existing files](https://kubernetes.io/docs/concepts/configuration/secret/#tls-secrets).

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: https-ingress-terminated-tls-example
spec:
  ingressClassName: nginx
  tls:
  - hosts:
      - https-example.foo.com
    secretName: testsecret-tls
  rules:
  - host: https-example.foo.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: <my-pubsubplus-service>
            port:
              name: tcp-rest
```

External requests shall be targeted to the ingress External-IP through the defined hostname (here `https-example.foo.com`) at the TLS port (443) and the specified path.


##### HTTPS with TLS re-encrypt at ingress

This only differs from above in that the request is forwarded to a TLS-encrypted PubSub+ service port. The broker must have TLS configured but there are no specific requirements for the broker certificate as the ingress does not enforce it.

The difference in the Ingress manifest is an NGINX-specific annotation marking that the backend is using TLS, and the service target port in the last line - it refers now to a TLS backend port:

```yaml
metadata:
  :
  annotations:
    nginx.ingress.kubernetes.io/backend-protocol: HTTPS
  :
spec:
  :
  rules:
  :
            port:
              name: tls-rest
```

##### General TCP over TLS with passthrough to broker

In this case the ingress does not terminate TLS, only provides routing to the broker Pod based on the hostname provided in the SNI extension of the Client Hello at TLS connection setup. Since it will pass through TLS traffic directly to the broker as opaque data, this enables the use of ingress for any TCP-based protocol using TLS as transport.

The TLS passthrough capability must be explicitly enabled on the NGINX ingress controller, as it is off by default. This can be done by editing the `ingress-nginx-controller` "Deployment" in the `ingress-nginx` namespace.
1. Open the controller for editing: `kubectl edit deployment ingress-nginx-controller --namespace ingress-nginx`
2. Search where the `nginx-ingress-controller` arguments are provided, insert `--enable-ssl-passthrough` to the list and save. For more information refer to the [NGINX User Guide](https://kubernetes.github.io/ingress-nginx/user-guide/tls/#ssl-passthrough). Also note the potential performance impact of using SSL Passthrough mentioned here.

The Ingress manifest specifies "passthrough" by adding the `nginx.ingress.kubernetes.io/ssl-passthrough: "true"` annotation.

The deployed PubSub+ broker(s) must have TLS configured with a certificate that includes DNS names in CN and/or SAN, that match the host used. In the example the broker server certificate may specify the host `*.broker1.bar.com`, so multiple services can be exposed from `broker1`, distinguished by the host FQDN.

The protocol client must support SNI. It depends on the client if it uses the server certificate CN or SAN for host name validation. Most recent clients use SAN, for example the PubSub+ Java API requires host DNS names in the SAN when using SNI.

With above, an ingress example looks following:

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: ingress-passthrough-tls-example
  annotations:
    nginx.ingress.kubernetes.io/ssl-passthrough: "true"
spec:
  ingressClassName: nginx
  rules:
  - host: smf.broker1.bar.com
    http:
      paths:
      - backend:
          service:
            name: <my-pubsubplus-service>
            port:
              name: tls-smf
        path: /
        pathType: ImplementationSpecific
```
External requests shall be targeted to the ingress External-IP through the defined hostname (here `smf.broker1.bar.com`) at the TLS port (443) with no path required.

#### Using pod label "active" to identify the active event broker node

This section provides more information about what is required to achieve the correct label for the pod hosting the active event broker node.

Use `kubectl get pods --show-labels` to check for the status of the "active" label. In a stable deployment, one of the message routing nodes with ordinal 0 or 1 shall have the label `active=true`. You can find out if there is an issue by [checking events](#viewing-events) for related ERROR reported.

This label is set by the `readiness_check.sh` script in `pubsubplus/templates/solaceConfigMap.yaml`, triggered by the StatefulSet's readiness probe. For this to happen the followings are required:

- the Solace pods must be able to communicate with each-other at port 8080 and internal ports using the Service-Discovery service.
- the Kubernetes service account associated with the Solace pod must have sufficient rights to patch the pod's label when the active event broker is service ready
- the Solace pods must be able to communicate with the Kubernetes API at `kubernetes.default.svc.cluster.local` at port $KUBERNETES_SERVICE_PORT. You can find out the address and port by [SSH into the pod](#ssh-access-to-individual-message-brokers).

### Enabling use of TLS to access broker services

#### Setting up TLS

Default deployment does not have TLS over TCP enabled to access broker services. Although the exposed `service.ports` include ports for secured TCP, only the insecure ports can be used by default.

To enable accessing services over TLS a server key and certificate must be configured on the broker.

It is assumed that a provider out of scope of this document will be used to create a server key and certificate for the event broker, that meet the [requirements described in the Solace Documentation](https://docs.solace.com/Configuring-and-Managing/Managing-Server-Certs.htm). If the server key is password protected it shall be transformed to an unencrypted key, e.g.:  `openssl rsa -in encryedprivate.key -out unencryed.key`.

The server key and certificate must be packaged in a Kubernetes secret, for example by [creating a TLS secret](https://kubernetes.io/docs/concepts/configuration/secret/#tls-secrets). Example:
```
kubectl create secret tls <my-tls-secret> --key="<my-server-key-file>" --cert="<my-certificate-file>"
```

This secret name and related parameters shall be specified when deploying the PubSub+ Helm chart:
```
tls:
  enabled: true    # set to false by default
  serverCertificatesSecret: <my-tls-secret> # replace by the actual name
  certFilename:    # optional, default if not provided: tls.crt 
  certKeyFilename: # optional, default if not provided: tls.key
```

> Note: ensure filenames are matching the files reported from running `kubectl describe secret <my-tls-secret>`.

Here is an example new deployment with TLS enabled using default `certFilename` and `certKeyFilename`:
```
helm install my-release solacecharts/pubsubplus \
--set tls.enabled=true,tls.serverCertificatesSecret=<my-tls-secret>
```

Important: it is not possible to update an existing deployment to enable TLS that has been created without TLS enabled, by simply using the [modify deployment](#modifying-or-upgrading-a-deployment) procedure. In this case, for the first time, certificates need to be [manually loaded and set up](//docs.solace.com/Configuring-and-Managing/Managing-Server-Certs.htm) on each broker node. After that it is possible to use `helm upgrade` with a secret specified.
It is also important to note that because the TLS/SSL configuration are not included in the global [backup](https://docs.solace.com/Admin/Restoring-Config-Files.htm), this configuration can not be restored.

#### Rotating the server key

In the event the server key or certificate need to be rotated a new Kubernetes secret must be created, which may require deleting and recreating the old secret if using the same name.

Next, if using the same secret name, the broker Pods need to be restarted, one at a time waiting to reach `1/1` availability before continuing on the next one: starting with the Monitor (ordinal -2), followed by the node in backup role with `active=false` label, and finally the third node. If using a new secret name, the [modify deployment](#modifying-or-upgrading-a-deployment) procedure can be used and an automatic rolling update will follow these steps restarting the nodes one at a time.

> Note: a pod restart will result in provisioning the server certificate from the secret again so it will revert back from any other server certificate that may have been provisioned on the broker through other mechanism.

### The PubSub+ Software Event Broker Docker image

The `image.repository` and `image.tag` parameters combined specify the PubSub+ Software Event Broker Docker image to be used for the deployment. They can either point to an image in a public or a private Docker container registry. 

#### Using a public registry

The default values are `solace/solace-pubsub-standard/` and `latest`, which is the free PubSub+ Software Event Broker Standard Edition from the [public Solace Docker Hub repo](//hub.docker.com/r/solace/solace-pubsub-standard/). It is generally recommended to set `image.tag` to a specific build for traceability purposes.

#### Using private registries

The following steps are applicable if using a private Docker container registry (e.g.: GCR, ECR or Harbor):
1. Get the Solace PubSub+ event broker Docker image tar.gz archive
2. Load the image into the private Docker registry 

To get the PubSub+ Software Event Broker Docker image URL, go to the Solace Developer Portal and download the Solace PubSub+ Software Event Broker as a **docker** image or obtain your version from Solace Support.

| PubSub+ Software Event Broker Standard<br/>Docker Image | PubSub+ Software Event Broker Enterprise Evaluation Edition<br/>Docker Image
| :---: | :---: |
| Free, up to 1k simultaneous connections,<br/>up to 10k messages per second | 90-day trial version, unlimited |
| [Download Standard docker image](http://dev.solace.com/downloads/ ) | [Download Evaluation docker image](http://dev.solace.com/downloads#eval ) |

To load the Solace PubSub+ Software Event Broker Docker image into a private Docker registry, follow the general steps below; for specifics, consult the documentation of the registry you are using.

* Prerequisite: local installation of [Docker](//docs.docker.com/get-started/ ) is required
* Login to the private registry:
```sh
sudo docker login <private-registry> ...
```
* First, load the image to the local docker registry:
```sh
# Options a or b depending on your Docker image source:
## Option a): If you have a local tar.gz Docker image file
sudo docker load -i <solace-pubsub-XYZ-docker>.tar.gz
## Option b): You can use the public Solace Docker image, such as from Docker Hub
sudo docker pull solace/solace-pubsub-standard:latest # or specific <TagName>
#
# Verify the image has been loaded and note the associated "IMAGE ID"
sudo docker images
```
* Tag the image with a name specific to the private registry and tag:
```sh
sudo docker tag <image-id> <private-registry>/<path>/<image-name>:<tag>
```
* Push the image to the private registry
```sh
sudo docker push <private-registry>/<path>/<image-name>:<tag>
```

Note that additional steps may be required if using signed images.

#### Using ImagePullSecrets for signed images

An additional ImagePullSecret may be required if using signed images from a private Docker registry, e.g.: Harbor.

Here is an example of creating an ImagePullSecret. Refer to your registry's documentation for the specific details of use.

```sh
kubectl create secret docker-registry <pull-secret-name> --dockerserver=<private-registry-server> \
  --docker-username=<registry-user-name> --docker-password=<registry-user-password> \
  --docker-email=<registry-user-email>
```

Then set the `image.pullSecretName` chart value to `<pull-secret-name>`.

### Security considerations

#### Using Security Context

The event broker container already runs in non-privileged mode.

If `securityContext.enabled` is `true` (default) then the `securityContext.fsGroup` and `securityContext.runAsUser` settings define [the pod security context](//kubernetes.io/docs/tasks/configure-pod-container/security-context/).

If other settings control `fsGroup` and `runAsUser`, e.g: when using a [PodSecurityPolicy](//kubernetes.io/docs/concepts/policy/pod-security-policy/) or an Openshift "restricted" SCC, `securityContext.enabled` shall be set to `false` or ensure specified values do not conflict with the policy settings.

#### Enabling pod label "active" in a tight security environment

Services require [pod label "active"](#using-pod-label-active-to-identify-the-active-event-broker-node) of the serving event broker.
* In a controlled environment it may be necessary to add a [NetworkPolicy](//kubernetes.io/docs/concepts/services-networking/network-policies/ ) to enable [required communication](#using-pod-label-active-to-identify-the-active-event-broker-node).

#### Securing TLS server key and certificate

Using secrets for TLS server keys and certificates follows Kubernetes recommendations, however, particularly in a production environment, additional steps are required to ensure only authorized access to these secrets following Kubernetes industry best practices, including setting tight RBAC permissions and fixing possible security holes.

### User management considerations

#### Adding new users

The deployment comes with an existing user `admin`. Depending on how the installation is carried out, it should start with a random 
password or an existing one. Refer [here](#admin-password). The default `admin` user has `admin` CLI User Access Level. This means
an `admin` user can execute all CLI commands on the event broker which also includes controlling broker-wide authentication and authorization. They can also create other admin users. 

However, if there is need to set up a new CLI user, first directly access the event broker pod:

```sh
kubectl exec -it XXX-XXX-pubsubplus-<pod-ordinal> -- bash
```

once you have access to the Solace CLI, enter the following commands to create a new user:

```sh
solace> enable
solace# configure
solace(configure)# create username <new-user-name>
```

enter the following commands to set the CLI User and their access level. For a full list of all the available access levels refer to [this](https://docs.solace.com/Admin/CLI-User-Access-Levels.htm)

```sh
solace(configure/username) global-access-level <access-level>
solace(configure/username) change-password <password>
```

The new user will now be available for use via the CLI  

#### Changing user passwords

At the moment, we do not support changing the default `admin` user password. 
If there is a need to change the password of a user other than the `admin`. 

Directly access the event broker pod:

```sh
kubectl exec -it XXX-XXX-pubsubplus-<pod-ordinal> -- bash
```

get access to the Solace CLI and enter the following commands:

```sh
solace> enable
solace# configure
solace(configure)# username <user-name>
solace(configure/username) change-password <password>
```

## Deployment Prerequisites

### Platform and tools setup

#### Install the `kubectl` command-line tool

Refer to [these instructions](//kubernetes.io/docs/tasks/tools/install-kubectl/) to install `kubectl` if your environment does not already provide this tool or equivalent (like `oc` in OpenShift).

#### Perform any necessary Kubernetes platform-specific setup

This refers to getting your platform ready either by creating a new one or getting access to an existing one. Supported platforms include but are not restricted to:
* Amazon EKS
* Azure AKS
* Google GCP
* OpenShift
* MiniKube
* VMWare PKS

Check your platform running the `kubectl get nodes` command from your command-line client.

#### Install and setup the Helm package manager

The event broker can be deployed using Helm v3.
> Note: For Helm v2 support refer to [earlier versions of this quickstart](https://github.com/SolaceProducts/pubsubplus-kubernetes-helm-quickstart/releases).

The Helm v3 executable is available from https://github.com/helm/helm/releases . Further documentation is available from https://helm.sh/.

```shell
curl https://raw.githubusercontent.com/helm/helm/master/scripts/get-helm-3 | bash
```

## Deployment steps

As discussed in the [Overview](#overview), two types of deployments will be described:
* Deployment steps using Helm, as package manager
* Alternative Deployment with generating templates for the Kubernetes `kubectl` tool

### Deployment steps using Helm

The recommended way is to make use of published pre-packaged PubSub+ charts from Solace' public repo and customizing your deployment through [available chart parameters](/pubsubplus/README.md).

Add or refresh a local Solace `solacecharts` repo:
```bash
# Add new "solacecharts" repo
helm repo add solacecharts https://solaceproducts.github.io/pubsubplus-kubernetes-helm-quickstart/helm-charts
# Refresh if needed, e.g.: to use a recently published chart version
helm repo update solacecharts

# Install from the repo
helm install my-release solacecharts/pubsubplus
```

There are three Helm chart variants available with default small-size configurations:
1.	`pubsubplus-dev` - PubSub+ Software Event Broker for Developers (standalone)
2.	`pubsubplus` - PubSub+ Software Event Broker standalone, supporting 100 connections
3.	`pubsubplus-ha` - PubSub+ Software Event Broker HA, supporting 100 connections

Customization options are described in the [PubSub+ Software Event Broker Helm Chart](/pubsubplus/README.md#configuration) reference.

Also, refer to the [quick start guide](/README.md) for additional deployment details.

**More customization options**

If more customization than just using Helm parameters is required, you can create your own fork so templates can be edited:
```bash
# This creates a local directory from the published templates
helm fetch solacecharts/pubsubplus --untar
# Use the Helm chart from this directory
helm install ./pubsubplus
```
> Note: it is encouraged to raise a [GitHub issue](https://github.com/SolaceProducts/pubsubplus-kubernetes-helm-quickstart/issues/new) to possibly contribute your enhancements back to the project.

### Alternative Deployment with generating templates for the Kubernetes `kubectl` tool

This method will first generate installable Kubernetes templates from this project's Helm charts, then the templates can be installed using the Kubectl tool.

Note that later sections of this document about modifying, upgrading or deleting a Deployment using the Helm tool do not apply.

**Step 1: Generate Kubernetes templates for Solace event broker deployment**

1) Ensure Helm is locally installed.

2) Add or refresh a local Solace `solacecharts` repo:
```bash
# Add new "solacecharts" repo
helm repo add solacecharts https://solaceproducts.github.io/pubsubplus-kubernetes-helm-quickstart/helm-charts
# Refresh if needed, e.g.: to use a recently published chart version
helm repo update solacecharts
```

3) Generate the templates: 

First, consider if any [configurations](/pubsubplus/README.md#configuration) are required.
If this is the case then you can add overrides as additional `--set ...` parameters to the `helm template` command, or use an override YAML file.

```sh
# Create local copy
helm fetch solacecharts/pubsubplus --untar
# Create location for the generated templates
mkdir generated-templates
# In one of next sample commands replace my-release to the desired release name
#   a) Using all defaults:
helm template my-release --output-dir ./generated-templates ./pubsubplus
#   b) Example with configuration using --set
helm template my-release --output-dir ./generated-templates \
  --set solace.redundancy=true \
  ./pubsubplus
#   c) Example with configuration using --set
helm template my-release --output-dir ./generated-templates \
  -f my-values.yaml \
  ./pubsubplus

```
The generated set of templates are now available in the `generated-templates` directory.

**Step 2: Deploy the templates on the target system**

Assumptions: `kubectl` is deployed and configured to point to your Kubernetes cluster

1) Optionally, copy the `generated-templates` directory with contents if this is on a different host

2) Initiate the deployment:
```bash
kubectl apply --recursive -f ./generated-templates/pubsubplus
```
Wait for the deployment to complete, which is then ready to use.

3) To delete the deployment, execute:
```bash
kubectl delete --recursive -f ./generated-templates/pubsubplus
```



## Validating the Deployment

Now you can validate your deployment on the command line. In this example an HA configuration is deployed with pod/XXX-XXX-pubsubplus-0 being the active event broker/pod. The notation XXX-XXX is used for the unique release name, e.g: "my-release".

```sh
prompt:~$ kubectl get statefulsets,services,pods,pvc,pv
NAME                                     READY   AGE
statefulset.apps/my-release-pubsubplus   3/3     13m

NAME                                      TYPE           CLUSTER-IP    EXTERNAL-IP   PORT(S)                                                                                                                                                                   AGE
service/kubernetes                        ClusterIP      10.92.0.1     <none>        443/TCP                                                                                                                                                                   14d
service/my-release-pubsubplus             LoadBalancer   10.92.13.40   34.67.66.30   2222:30197/TCP,8080:30343/TCP,1943:32551/TCP,55555:30826/TCP,55003:30770/TCP,55443:32583/TCP,8008:32689/TCP,1443:32460/TCP,5672:31960/TCP,1883:32112/TCP,9000:30848/TCP   13m
service/my-release-pubsubplus-discovery   ClusterIP      None          <none>        8080/TCP,8741/TCP,8300/TCP,8301/TCP,8302/TCP                                                                                                                              13m

NAME                          READY   STATUS    RESTARTS   AGE
pod/my-release-pubsubplus-0   1/1     Running   0          13m
pod/my-release-pubsubplus-1   1/1     Running   0          13m
pod/my-release-pubsubplus-2   1/1     Running   0          13m

NAME                                                 STATUS   VOLUME                                     CAPACITY   ACCESS MODES   STORAGECLASS   AGE
persistentvolumeclaim/data-my-release-pubsubplus-0   Bound    pvc-6b0cd358-30c4-11ea-9379-42010a8000c7   30Gi       RWO            standard       13m
persistentvolumeclaim/data-my-release-pubsubplus-1   Bound    pvc-6b14bc8a-30c4-11ea-9379-42010a8000c7   30Gi       RWO            standard       13m
persistentvolumeclaim/data-my-release-pubsubplus-2   Bound    pvc-6b24b2aa-30c4-11ea-9379-42010a8000c7   30Gi       RWO            standard       13m

NAME                                                        CAPACITY   ACCESS MODES   RECLAIM POLICY   STATUS   CLAIM                                  STORAGECLASS   REASON   AGE
persistentvolume/pvc-6b0cd358-30c4-11ea-9379-42010a8000c7   30Gi       RWO            Delete           Bound    default/data-my-release-pubsubplus-0   standard                13m
persistentvolume/pvc-6b14bc8a-30c4-11ea-9379-42010a8000c7   30Gi       RWO            Delete           Bound    default/data-my-release-pubsubplus-1   standard                13m
persistentvolume/pvc-6b24b2aa-30c4-11ea-9379-42010a8000c7   30Gi       RWO            Delete           Bound    default/data-my-release-pubsubplus-2   standard                13m


prompt:~$ kubectl describe service my-release-pubsubplus
Name:                     my-release-pubsubplus
Namespace:                test
Labels:                   app.kubernetes.io/instance=my-release
                          app.kubernetes.io/managed-by=Tiller
                          app.kubernetes.io/name=pubsubplus
                          helm.sh/chart=pubsubplus-1.0.0
Annotations:              <none>
Selector:                 active=true,app.kubernetes.io/instance=my-release,app.kubernetes.io/name=pubsubplus
Type:                     LoadBalancer
IP:                       10.100.200.41
LoadBalancer Ingress:     34.67.66.30
Port:                     ssh  2222/TCP
TargetPort:               2222/TCP
NodePort:                 ssh  30197/TCP
Endpoints:                10.28.1.20:2222
:
:
```

Generally, all services including management and messaging are accessible through a Load Balancer. In the above example `34.67.66.30` is the Load Balancer's external Public IP to use.

> Note: When using MiniKube, there is no integrated Load Balancer. For a workaround, execute `minikube service XXX-XXX-solace` to expose the services. Services will be accessible directly using mapped ports instead of direct port access, for which the mapping can be obtained from `kubectl describe service XXX-XX-solace`.

### Gaining admin access to the event broker

There are [multiple management tools](//docs.solace.com/Management-Tools.htm ) available. The WebUI is the recommended simplest way to administer the event broker for common tasks.

#### Admin Password

A random admin password will be generated if it has not been provided at deployment using the `solace.usernameAdminPassword` parameter, refer to the the information from `helm status` how to retrieve it.

**Important:** Every time `helm install` or `helm upgrade` is called a new admin password will be generated, which may break an existing deployment. Therefore ensure to always provide the password from the initial deployment as `solace.usernameAdminPassword=<PASSWORD>` parameter to subsequent `install` and `upgrade` commands.

#### WebUI, SolAdmin and SEMP access

Use the Load Balancer's external Public IP at port 8080 to access these services.

#### Solace CLI access

If you are using a single event broker and are used to working with a CLI event broker console access, you can SSH into the event broker as the `admin` user using the Load Balancer's external Public IP:

```sh

$ssh -p 2222 admin@35.202.131.158
Solace PubSub+ Standard
Password:

Solace PubSub+ Standard Version 9.4.0.105

The Solace PubSub+ Standard is proprietary software of
Solace Corporation. By accessing the Solace PubSub+ Standard
you are agreeing to the license terms and conditions located at
//www.solace.com/license-software

Copyright 2004-2019 Solace Corporation. All rights reserved.

To purchase product support, please contact Solace at:
//dev.solace.com/contact-us/

Operating Mode: Message Routing Node

XXX-XXX-pubsubplus-0>
```

If you are using an HA deployment, it is better to access the CLI through the Kubernets pod and not directly via SSH.

* Loopback to SSH directly on the pod

```sh
kubectl exec -it XXX-XXX-pubsubplus-0  -- bash -c "ssh -p 2222 admin@localhost"
```

* Loopback to SSH on your host with a port-forward map

```sh
kubectl port-forward XXX-XXX-pubsubplus-0 62222:2222 &
ssh -p 62222 admin@localhost
```

This can also be mapped to individual event brokers in the deployment via port-forward:

```
kubectl port-forward XXX-XXX-pubsubplus-0 8081:8080 &
kubectl port-forward XXX-XXX-pubsubplus-1 8082:8080 &
kubectl port-forward XXX-XXX-pubsubplus-2 8083:8080 &
```

#### SSH access to individual event brokers

For direct access, use:

```sh
kubectl exec -it XXX-XXX-pubsubplus-<pod-ordinal> -- bash
```

### Testing data access to the event broker

To test data traffic though the newly created event broker instance, visit the Solace Developer Portal [APIs & Protocols](//www.solace.dev/ ). Under each option there is a Publish/Subscribe tutorial that will help you get started and provide the specific default port to use.

Use the external Public IP to access the deployment. If a port required for a protocol is not opened, refer to the [Modification example](#modification-example) how to open it up.

## Troubleshooting

### General Kubernetes troubleshooting hints
https://kubernetes.io/docs/tasks/debug-application-cluster/debug-application/

### Checking the reason for failed resources

Run `kubectl get statefulsets,services,pods,pvc,pv` to get an understanding of the state, then drill down to get more information on a failed resource to reveal  possible Kubernetes resourcing issues, e.g.:
```sh
kubectl describe pvc <pvc-name>
```

### Viewing logs

Detailed logs from the currently running container in a pod:
```sh
kubectl logs XXX-XXX-pubsubplus-0 -f  # use -f to follow live
```

It is also possible to get the logs from a previously terminated or failed container:
```sh
kubectl logs XXX-XXX-pubsubplus-0 -p
```

Filtering on bringup logs (helps with initial troubleshooting):
```sh
kubectl logs XXX-XXX-pubsubplus-0 | grep [.]sh
```

### Viewing events

Kubernetes collects [all events for a cluster in one pool](//kubernetes.io/docs/tasks/debug-application-cluster/events-stackdriver ). This includes events related to the PubSub+ deployment.

It is recommended to watch events when creating or upgrading a Solace deployment. Events clear after about an hour. You can query all available events:

```sh
kubectl get events -w # use -w to watch live
```

### PubSub+ Software Event Broker troubleshooting

#### Pods stuck in not enough resources

If pods stay in pending state and `kubectl describe pods` reveals there are not enough memory or CPU resources, check the [resource requirements of the targeted scaling tier](#cpu-and-memory-requirements) of your deployment and ensure adequate node resources are available.

#### Pods stuck in no storage

Pods may also stay in pending state because [storage requirements](#storage) cannot be met. Check `kubectl get pv,pvc`. PVCs and PVs should be in bound state and if not then use `kubectl describe pvc` for any issues.

Unless otherwise specified, a default storage class must be available for default PubSub+ deployment configuration.
```bash
kubectl get storageclasses
```

#### Pods stuck in CrashLoopBackoff, Failed or Not Ready

Pods stuck in CrashLoopBackoff, or Failed, or Running but not Ready "active" state, usually indicate an issue with available Kubernetes node resources or with the container OS or the event broker process start.

* Try to understand the reason following earlier hints in this section.
* Try to recreate the issue by deleting and then reinstalling the deployment - ensure to remove related PVCs if applicable as they would mount volumes with existing, possibly outdated or incompatible database - and watch the [logs](#viewing-logs) and [events](#viewing-events) from the beginning. Look for ERROR messages preceded by information that may reveal the issue.

#### No Pods listed

If no pods are listed related to your deployment check the StatefulSet for any clues:
```
kubectl describe statefulset my-release-pubsubplus
```

#### Security constraints

Your Kubernetes environment's security constraints may also impact successful deployment. Review the [Security considerations](#security-considerations) section.

## Modifying or upgrading a Deployment

Use the `helm upgrade` command to upgrade/modify the event broker deployment: request the required modifications to the chart in passing the new/changed parameters or creating an upgrade `<values-file>` YAML file. When chaining multiple `-f <values-file>` to Helm, the override priority will be given to the last (right-most) file specified.

For both version upgrade and modifications, the "RollingUpdate" strategy of the Kubernetes StatefulSet applies: pods in the StatefulSet are restarted with new values in reverse order of ordinals, which means for PubSubPlus first the monitoring node (ordinal 2), then backup (ordinal 1) and finally the primary node (ordinal 0).

For the next examples, assume a deployment has been created with some initial overrides for a development HA cluster:
```bash
helm install my-release solacecharts/pubsubplus --set solace.size=dev,solace.redundancy=true
```

#### Getting the currently used parameter values

Currently used parameter values are the default chart parameter values overlayed with value-overrides.

To get the default chart parameter values, check `helm show values solacecharts/pubsubplus`.

To get the current value-overrides, execute:
```
$ helm get values my-release
USER-SUPPLIED VALUES:
solace:
  redundancy: true
  size: dev
```
**Important:** this may not show, but be aware of an additional non-default parameter:
```
solace:
  usernameAdminPassword: jMzKoW39zz   # The value is just an example
```
This has been generated at the initial deployment if not specified and must be used henceforth for all change requests, to keep the same. See related note in the [Admin Password section](#admin-password).

#### Upgrade example

To **upgrade** the version of the event broker running within a Kubernetes cluster:

- Add the new version of the event broker to your container registry, then
- Either:
  * Set the new image in the Helm upgrade command, also ensure to include the original overrides: 
```bash
helm upgrade my-release solacecharts/pubsubplus \
  --set solace.size=dev,solace.redundancy=true,solace.usernameAdminPassword: jMzKoW39zz \
  --set image.repository=<repo>/<project>/solace-pubsub-standard,image.tag=NEW.VERSION.XXXXX,image.pullPolicy=IfNotPresent
```
  * Or create a simple `version-upgrade.yaml` file and use that to upgrade the release:
```bash
tee ./version-upgrade.yaml <<-EOF   # include original and new overrides
solace:
  redundancy: true
  size: dev
  usernameAdminPassword: jMzKoW39zz
image:
  repository: <repo>/<project>/solace-pubsub-standard
  tag: NEW.VERSION.XXXXX
  pullPolicy: IfNotPresent
EOF
helm upgrade my-release solacecharts/pubsubplus -f version-upgrade.yaml
```
> Note: upgrade will begin immediately, in the order of pod 2, 1 and 0 (Monitor, Backup, Primary) taken down for upgrade in an HA deployment. This will affect running event broker instances, result in potentially multiple failovers and requires connection-retries configured in the client.

#### Modification example

Similarly, to **modify** deployment parameters, you need pass modified value-overrides. Passing the same value-overrides to upgrade will result in no change.

In this example we will add the AMQP encrypted (TLS) port to the loadbalancer - it is not included by default.

First [look up](//docs.solace.com/Configuring-and-Managing/Default-Port-Numbers.htm#Software) the port number for MQTT TLS: the required port is 5671.

Next, create an update file with the additional contents:
```bash
tee ./port-update.yaml <<-EOF   # :
service:
  ports:
    - servicePort: 5671
      containerPort: 5671
      protocol: TCP
      name: amqptls
EOF
```

Now upgrade the deployment, passing the changes. This time the original `--set` value-overrides are combined with the override file:
```bash
helm upgrade my-release solacecharts/pubsubplus \
  --set solace.size=dev,solace.redundancy=true,solace.usernameAdminPassword: jMzKoW39zz \
  --values port-update.yaml
```

## Re-installing a Deployment

If using *persistent* storage broker data will not be deleted upon `helm delete`.

In this case the deployment can be reinstalled and continue from the point before the `helm delete` command was executed by running `helm install` again, using the **same** release name and parameters as the previous run. This includes explicitly providing the same admin password as before.

```
# Initial deployment:
helm install my-release solacecharts/pubsubplus --set solace.size=dev,solace.redundancy=true
# This will auto-generate an admin password
# Retrieve the admin password, follow instructions from the output of "helm status", section Admin credentials
# Delete this deployment
helm delete my-release
# Reinstall deployment, assuming persistent storage. Notice the admin password specified
helm install my-release solacecharts/pubsubplus --set solace.size=dev,solace.redundancy=true,solace.usernameAdminPassword=jMzKoW39zz
# Original deployment is now back up
```

## Deleting a Deployment

Use Helm to delete a deployment, also called a release:
```
helm delete my-release
```

Check what has remained from the deployment:
```
kubectl get statefulsets,services,pods,pvc,pv
```

> Note: Helm will not clean up PVCs and related PVs. Use `kubectl delete` to delete PVCs is associated data is no longer required.

## Backing Up and Restore

The preferred way of backing up and restoring your deployment is by backing up and restoring the message vpns. 
This is because of certain limitations of the system-wide backup and restore. For example TLS/SSL configuration are not included in system-wide backup hence configurations related to it will be lost.

A detailed guide to perform backing up and restore of message vpns can be found [here](https://docs.solace.com/Features/VPN/Backing-Up-and-Restoring-VPNs.htm).






