# Solace PubSub+ Software Event Broker on Kubernetes Deployment Documentation

This document provide detailed information for deploying Solace PubSub+ Software Event Broker on Kubernetes.

* For a hands-on quick start, refer to the [Quick Start guide](/README.md).
* For the `pubsubplus` Helm chart configuration options, refer to the [PubSub+ Software Event Broker Helm Chart Reference](/pubsubplus/README.md).

This document is applicable to any platform supporting Kubernetes.

Contents:
  * [**The Solace PubSub+ Software Event Broker**](#the-solace-pubsub-software-event-broker)
  * [**Overview**](#overview)
  * [**PubSub+ Event Broker Deployment Considerations**](#pubsub-event-broker-deployment-considerations)
    + [Deployment scaling](#deployment-scaling)
    + [CPU and Memory Requirements](#cpu-and-memory-requirements)
    + [Disk Storage](#disk-storage)
      - [Using the default or an existing storage class](#using-the-default-or-an-existing-storage-class)
      - [Creating a new storage class](#creating-a-new-storage-class)
      - [Using an existing PVC (Persistent Volume Claim)](#using-an-existing-pvc-persistent-volume-claim-)
      - [Using a pre-created provider-specific volume](#using-a-pre-created-provider-specific-volume)
    + [Exposing the PubSub+ Event Broker Services](#exposing-the-pubsub-event-broker-services)
      - [Using pod label "active" to identify the active event broker node](#using-pod-label-active-to-identify-the-active-event-broker-node)
    + [The PubSub+ Docker image](#the-pubsub-docker-image)
      - [Using a public registry](#using-a-public-registry)
      - [Using private registries](#using-private-registries)
      - [Using ImagePullSecrets for signed images](#using-imagepullsecrets-for-signed-images)
    + [Security considerations](#security-considerations)
      - [Using Security Context](#using-security-context)
      - [Securing Helm v2](#securing-helm-v2)
      - [Enabling pod label "active" in a tight security environment](#enabling-pod-label-active-in-a-tight-security-environment)
  * [**Deployment Prerequisites**](#deployment-prerequisites)
    + [Platform and tools setup](#platform-and-tools-setup)
      - [Install the `kubectl` command-line tool](#install-the-kubectl-command-line-tool)
      - [Perform any necessary Kubernetes platform-specific setup](#perform-any-necessary-kubernetes-platform-specific-setup)
      - [Install and setup the Helm package manager](#install-and-setup-the-helm-package-manager)
        * [Helm v2](#helm-v2)
        * [Helm v3](#helm-v3)
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




## The Solace PubSub+ Software Event Broker

The [PubSub+ Software Event Broker](https://solace.com/products/event-broker/) of the [Solace PubSub+ Platform](https://solace.com/products/platform/) efficiently streams event-driven information between applications, IoT devices and user interfaces running in the cloud, on-premises, and hybrid environments using open APIs and protocols like AMQP, JMS, MQTT, REST and WebSocket. It can be installed into a variety of public and private clouds, PaaS, and on-premises environments, and brokers in multiple locations can be linked together in an [event mesh](https://solace.com/what-is-an-event-mesh/) to dynamically share events across the distributed enterprise.

## Overview

This document assumes a basic understanding of [Kubernetes concepts](https://kubernetes.io/docs/concepts/).

For an example deployment diagram, check out the [PubSub+ Event Broker on Google Kubernetes Engine (GKE) quickstart](https://github.com/SolaceProducts/pubsubplus-gke-quickstart#how-to-deploy-solace-pubsub-software-event-broker-onto-gke).

Multiple YAML templates define the PubSub+ Kubernetes deployment with several parameters as deployment options. The templates are packaged as the `pubsubplus` [Helm chart](//helm.sh/docs/topics/charts/) to enable easy customization by only specifying the non-default parameter values, without the need to edit the template files.

There are two deployment options described in this document:
* The recommended option is to use the [Kubernetes Helm tool](https://github.com/helm/helm/blob/master/README.md), which can also manage your deployment's lifecycle, including upgrade and delete.
* Another option is to generate a set of templates with customized values from the PubSub+ Helm chart and then use the Kubernetes native `kubectl` tool to deploy. The deployment will use the authorizations of the requesting user. However, in this case, Helm will not be able to manage your Kubernetes rollouts lifecycle.

The next sections will provide details on the PubSub+ Helm chart, dependencies and customization options, followed by [deployment prerequisites](#deployment-prerequisites) and the actual [deployment steps](#deployment-steps).

## PubSub+ Software Event Broker Deployment Considerations

The following diagram illustrates the template organization used for the PubSub+ Deployment chart. Note that the minimum is shown in this diagram to give you some background regarding the relationships and major functions.
![alt text](/docs/images/template_relationship.png "`pubsubplus` chart template relationship")

The StatefulSet template controls the pods of a PubSub+ Software Event Broker deployment. It also mounts the scripts from the ConfigMap and the files from the Secrets and maps the event broker data directories to a storage volume through a StorageClass, if configured. The Service template provides the event broker services at defined ports. The Service-Discovery template is only used internally, so pods in a PubSub+ event broker redundancy group can communicate with each other in an HA setting.

All the `pubsubplus` chart parameters are documented in the [PubSub+ Software Event Broker Helm Chart](/pubsubplus/README.md#configuration) reference.

### Deployment scaling

Solace PubSub+ Software Event Broker event broker can be vertically scaled by specifying the [number of concurrent client connections](//docs.solace.com/Configuring-and-Managing/SW-Broker-Specific-Config/System-Scaling-Parameters.htm#max-client-connections), controlled by the `solace.size` chart parameter.

Depending on the `solace.redundancy` parameter, one event router pod is deployed in a single-node standalone deployment or three pods if deploying a [High-Availability (HA) group](//docs.solace.com/Overviews/SW-Broker-Redundancy-and-Fault-Tolerance.htm).

Horizontal scaling is possible through [connecting multiple deployments](//docs.solace.com/Overviews/DMR-Overview.htm).

### CPU and Memory Requirements

The following CPU and memory requirements (for each pod) are summarized here from the [Solace documentation](//docs.solace.com/Configuring-and-Managing/SW-Broker-Specific-Config/System-Resource-Requirements.htm#res-req-container) for the possible `pubsubplus` chart `solace.size` parameter values:
* `dev`: no guaranteed performance, minimum requirements: 1 CPU, 3.4 GiB memory
* `prod100`: up to 100 connections, minimum requirements: 2 CPU, 3.4 GiB memory
* `prod1k`: up to 1,000 connections, minimum requirements: 2 CPU, 6.4 GiB memory
* `prod10k`: up to 10,000 connections, minimum requirements: 4 CPU, 12.2 GiB memory
* `prod100k`: up to 100,000 connections, minimum requirements: 8 CPU, 30.3 GiB memory
* `prod200k`: up to 200,000 connections, minimum requirements: 12 CPU, 51.4 GiB memory

### Disk Storage

The [PubSub+ deployment uses disk storage](//docs.solace.com/Configuring-and-Managing/Configuring-Storage.htm#Storage-) for logging, configuration, guaranteed messaging and other purposes, allocated from Kubernetes volumes.

Storage size (`storage.size` parameter) requirements for the scaling tiers:
* `dev`: no guaranteed performance: 5GB
* `prod100`: up to 100 connections, 7GB
* `prod1k`: up to 1,000 connections, 14GB
* `prod10k`: up to 10,000 connections, 18GB
* `prod100k`: up to 100,000 connections, 30GB
* `prod200k`: up to 200,000 connections, 34GB

Using a persistent storage is recommended, otherwise if pod-local storage is used data will be lost with the loss of a pod. The `storage.persistent` parameter is set to `true` by default.

The `pubsubplus` chart supports allocation of new storage volumes or mounting volumes with existing data. To avoid data corruption ensure to allocate clean new volumes for new deployments.

The recommended default allocation is to use Kubernetes [Storage Classes](//kubernetes.io/docs/concepts/storage/storage-classes/) utilizing [Dynamic Volume Provisioning](//kubernetes.io/docs/concepts/storage/dynamic-provisioning/). The `pubsubplus` chart deployment will create a Persistent Volume Claim (PVC) specifying the size and the Storage Class of the requested volume and a Persistent Volume (PV) that meets the requirements will be allocated. Both the PVC and PV names will be linked to the deployment's name. When deleting the event broker pod(s) or even the entire deployment, the PVC and the allocated PV will not be deleted, so potentially complex configuration is preserved. They will be re-mounted and reused with the existing configuration when a new pod starts (controlled by the StatefulSet, automatically matched to the old pod even in an HA deployment) or deployment with the same as the old name is started. Explicitly delete a PVC if no longer needed, which will delete the corresponding PV - refer to [Deleting a Deployment](#deleting-a-deployment).

Instead of using a storage class, the `pubsubplus` chart also allows you describe how to assign storage by adding your own YAML fragment in the `storage.customVolumeMount` parameter. The fragment is inserted for the `data` volume in the `{spec.template.spec.volumes}` section of the ConfigMap. Note that in this case the `storage.useStorageClass` parameter is ignored.

Followings are examples of how to specify parameter values in common use cases:

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

### Exposing the PubSub+ Software Event Broker Services

[PubSub+ services](//docs.solace.com/Configuring-and-Managing/Default-Port-Numbers.htm#Software) can be exposed through one of the [Kubernetes service types](//kubernetes.io/docs/concepts/services-networking/service/#publishing-services-service-types) by specifying the `service.type` parameter:

* LoadBalancer - an external load balancer (default)
* NodePort
* ClusterIP

To support [Internal load balancers](//kubernetes.io/docs/concepts/services-networking/service/#internal-load-balancer), provider-specific service annotation may be added through defining the `service.annotations` parameter.

The `service.ports` parameter defines the services exposed. It specifies the event broker `containerPort` that provides the service and the mapping to the `servicePort` where the service can be accessed when using LoadBalancer or ClusterIP. Note that there is no control over which port services are mapped when using NodePort.

When using Helm to initiate a deployment, notes will be provided on the screen about how to obtain the service addresses and ports specific to your deployment - follow the "Services access" section of the notes. 

A deployment is ready for service requests when there is a Solace pod that is running, `1/1` ready, and the pod's label is "active=true." The exposed `pubsubplus` service will forward traffic to that active event broker node. **Important**: service means here [Guaranteed Messaging level of  Quality-of-Service (QoS) of event messages persistence](//docs.solace.com/PubSub-Basics/Guaranteed-Messages.htm). Messaging traffic will not be forwarded if service level is degraded to [Direct Messages](//docs.solace.com/PubSub-Basics/Direct-Messages.htm) only.

#### Using pod label "active" to identify the active event broker node

This section provides more information about what is required to achieve the correct label for the pod hosting the active event broker node.

Use `kubectl get pods --show-labels` to check for the status of the "active" label. In a stable deployment, one of the message routing nodes with ordinal 0 or 1 shall have the label `active=true`. You can find out if there is an issue by [checking events](#viewing-events) for related ERROR reported.

This label is set by the `readiness_check.sh` script in `pubsubplus/templates/solaceConfigMap.yaml`, triggered by the StatefulSet's readiness probe. For this to happen the followings are required:

- the Solace pods must be able to communicate with each-other at port 8080 and internal ports using the Service-Discovery service.
- the Kubernetes service account associated with the Solace pod must have sufficient rights to patch the pod's label when the active event broker is service ready
- the Solace pods must be able to communicate with the Kubernetes API at `kubernetes.default.svc.cluster.local` at port $KUBERNETES_SERVICE_PORT. You can find out the address and port by [SSH into the pod](#ssh-access-to-individual-message-brokers).

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

#### Securing Helm v2

Using current Helm v2, Helm's server-side component Tiller must be installed in your Kubernetes environment with rights granted to manage deployments. By default, Tiller is deployed in a permissive configuration. There are best practices to secure Helm and Tiller, and they need to be applied carefully if strict security is required; for example, in a production environment.

[Securing your Helm Installation](//v2.helm.sh/docs/using_helm/#securing-your-helm-installation ) provides an overview of the Tiller-related security issues and recommended best practices.

Particularly, the [Role-based Access Control section of the Helm documentation](//v2.helm.sh/docs/using_helm/#role-based-access-control) provides options that should be used in RBAC-enabled Kubernetes environments (v1.6+).

#### Enabling pod label "active" in a tight security environment

Services require [pod label "active"](#using-pod-label-active-to-identify-the-active-event-broker-node) of the serving event broker.
* In a controlled environment it may be necessary to add a [NetworkPolicy](//kubernetes.io/docs/concepts/services-networking/network-policies/ ) to enable [required communication](#using-pod-label-active-to-identify-the-active-event-broker-node).


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

The event broker can be deployed using both Helm v2 and Helm v3. Helm v3 is recommended as it offers better security and it is actively maintained.

If `helm version` fails on your command-line client then this may involve installing Helm and/or if using Helm v2 then also deploying/redeploying Tiller, its in-cluster operator.

##### Helm v2

1. Install the Helm client following [your platform-specific instructions](//v2.helm.sh/docs/using_helm/#installing-the-helm-client ). For Linux, you can use:
```shell
curl -sSL https://raw.githubusercontent.com/helm/helm/master/scripts/get | bash
```

2. Deploy Tiller to manage your deployment. The following script is based on [the Example: Service account with cluster-admin role](//v2.helm.sh/docs/using_helm/#example-service-account-with-cluster-admin-role ).

**Important:** this will grant Tiller `cluster-admin` privileges to enable getting started on most platforms. This should be more secured for Production environments and may already fail in a restricted security environment. For options, see section [Security considerations](#security-considerations).

```shell
kubectl -n kube-system create serviceaccount tiller
kubectl create clusterrolebinding tiller --clusterrole cluster-admin --serviceaccount=kube-system:tiller
helm init --wait --service-account=tiller  --upgrade
```

If you are connecting to an environment where Helm was already installed from another command line client, just re-run the init part:
 ```shell
helm init --wait --service-account=tiller  --upgrade
```

##### Helm v3

The Helm v3 executable is available from https://github.com/helm/helm/releases . Installation of Tiller is no longer required. Ensure that your v3 installation does not conflict with an existing Helm v2 installation. Further documentation is available from https://helm.sh/.

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
helm repo add solacecharts https://solaceproducts.github.io/pubsubplus-kubernetes-quickstart/helm-charts
# Refresh if needed, e.g.: to use a recently published chart version
helm repo update solacecharts

# Install from the repo
## Using Helm v2:
helm install  --name my-release solacecharts/pubsubplus
## Or using Helm v3:
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
> Note: it is encouraged to raise a [GitHub issue](https://github.com/SolaceProducts/pubsubplus-kubernetes-quickstart/issues/new) to possibly contribute your enhancements back to the project.

### Alternative Deployment with generating templates for the Kubernetes `kubectl` tool

This is for users who don't wish to install the Helm v2 server-side Tiller on the Kubernetes cluster.

This method will first generate installable Kubernetes templates from this project's Helm charts, then the templates can be installed using the Kubectl tool.

Note that later sections of this document about modifying, upgrading or deleting a Deployment using the Helm tool do not apply.

**Step 1: Generate Kubernetes templates for Solace event broker deployment**

1) Ensure [Helm v2] i(#helm-v2) is locally installed. Note that this is the local client only, no server-side deployment of Tiller is necessary.

2) Add or refresh a local Solace `solacecharts` repo:
```bash
# Add new "solacecharts" repo
helm repo add solacecharts https://solaceproducts.github.io/pubsubplus-kubernetes-quickstart/helm-charts
# Refresh if needed, e.g.: to use a recently published chart version
helm repo update solacecharts
```

3) Generate the templates: 

First, consider if any [configurations](/pubsubplus/README.md#configuration) are required.
If this is the case then you can add overrides as additional `--set ...` parameters to the `helm template` command, or use an override YAML file.

```sh
# Create local copy - in Helm v2 "helm template" only works with local repositories.
helm fetch solacecharts/pubsubplus --untar
# Create location for the generated templates
mkdir generated-templates
# In one of next sample commands replace my-release to the desired release name
#   a) Using all defaults:
helm template --name my-release --output-dir ./generated-templates ./pubsubplus
#   b) Example with configuration using --set
helm template --name my-release --output-dir ./generated-templates \
  --set solace.redundancy=true \
  ./pubsubplus
#   c) Example with configuration using --set
helm template --name my-release --output-dir ./generated-templates \
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
**Important:** this will not show, but be aware of an additional non-default parameter:
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








