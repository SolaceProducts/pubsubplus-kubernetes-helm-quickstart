# Solace PubSub+ Event Broker on Kubernetes Deployment Guide

This is a detailed documentation of deploying Solace PubSub+ Event Broker on Kubernetes.

* For a hands-on quick start, refer to the [Quick Start guide](/README.md).
* For the `pubsubplus` Helm chart configuration reference, refer to the [PubSub+ Helm Chart](/pubsubplus/README.md).

This document is applicable to any platform supporting Kubernetes.

Contents:
  * [The Solace PubSub+ Software Event Broker](#the-solace-pubsub-software-event-broker)
  * [Overview](#overview)
  * [PubSub+ Helm Chart Deployment Considerations](#pubsub-helm-chart-deployment-considerations)
    + [Deployment scaling](#deployment-scaling)
    + [CPU and Memory Requirements](#cpu-and-memory-requirements)
    + [Disk Storage](#disk-storage)
      - [Using the default or an existing storage class](#using-the-default-or-an-existing-storage-class)
      - [Creating a storage class](#creating-a-storage-class)
      - [Using an existing PVC](#using-an-existing-pvc)
      - [Using a pre-created provider-specific volume](#using-a-pre-created-provider-specific-volume)
    + [Exposing the PubSub+ Event Broker Services](#exposing-the-pubsub-event-broker-services)
      - [Using pod label "active" to identify the active event broker node](#using-pod-label-active-to-identify-the-active-event-broker-node)
  * [Deployment Prerequisites](#deployment-prerequisites)
    + [Platform and tools setup](#platform-and-tools-setup)
      - [Perform any necessary platform-specific setup](#perform-any-necessary-platform-specific-setup)
      - [Install the `kubectl` command-line tool](#install-the-kubectl-command-line-tool)
      - [Install and setup the Helm package manager](#install-and-setup-the-helm-package-manager)
      - [Restore Helm](#restore-helm)
      - [Using Helm v3](#using-helm-v3)
    + [PubSub+ Docker image](#pubsub-docker-image)
    + [Create and use ImagePullSecrets for signed images](#create-and-use-imagepullsecrets-for-signed-images)
    + [Persistent Storage](#persistent-storage)
    + [Security considerations](#security-considerations)
      - [Privileged false](#privileged-false)
      - [Securing Helm](#securing-helm)
      - [Enabling pod label "active" in a tight security environment](#enabling-pod-label-active-in-a-tight-security-environment)
  * [Deployment options](#deployment-options)
    + [Deployment steps using Helm](#deployment-steps-using-helm)
    + [Alternative Deployment with generating templates for the Kubernetes `kubectl` tool](#alternative-deployment-with-generating-templates-for-the-kubernetes-kubectl-tool)
      - [Step 1: Generate Kubernetes templates for Solace event broker deployment](#step-1-generate-kubernetes-templates-for-solace-event-broker-deployment)
      - [Step 2: Deploy the templates on the target system](#step-2-deploy-the-templates-on-the-target-system)
  * [Validating the Deployment](#validating-the-deployment)
    + [Gaining admin access to the message broker](#gaining-admin-access-to-the-message-broker)
      - [WebUI, SolAdmin and SEMP access](#webui-soladmin-and-semp-access)
      - [Solace CLI access](#solace-cli-access)
      - [SSH access to individual message brokers](#ssh-access-to-individual-message-brokers)
    + [Testing data access to the message broker](#testing-data-access-to-the-message-broker)
  * [Troubleshooting](#troubleshooting)
    + [Viewing logs](#viewing-logs)
    + [Viewing events](#viewing-events)
    + [Solace event broker troubleshooting](#solace-event-broker-troubleshooting)
      - [General troubleshooting hints](#general-troubleshooting-hints)
      - [Pods stuck not enough resources](#pods-stuck-not-enough-resources)
      - [Pods stuck no storage](#pods-stuck-no-storage)
      - [Pods stuck in CrashLoopBackoff or Failed](#pods-stuck-in-crashloopbackoff-or-failed)
      - [Security constraints](#security-constraints)
  * [Modifying or upgrading a Deployment](#modifying-or-upgrading-a-deployment)
  * [Deleting a Deployment](#deleting-a-deployment)
  * [Additional notes](#additional-notes)

## The Solace PubSub+ Software Event Broker

The [PubSub+ Advanced Event Broker](https://solace.com/products/event-broker/) of the [Solace PubSub+ Platform](https://solace.com/products/platform/) efficiently streams event-driven information between applications, IoT devices and user interfaces running in cloud, on-premise, and hybrid environments using open APIs and protocols like AMQP, JMS, MQTT, REST and WebSocket. It can be installed into a variety of public and private clouds, PaaS, and on-premise environments, and brokers in multiple locations can be linked together in an [Event Mesh](https://solace.com/what-is-an-event-mesh/) to dynamically share events across the distributed enterprise.

## Overview

The PubSub+ Kubernetes deployment is defined by multiple YAML templates with several parameters as deployment options. The templates are packaged as the `pubsubplus` [Helm chart](https://helm.sh/docs/developing_charts/) to enable easy customization through only specifying the non-default parameter values, without the need to edit the template files.

There are two deployment options described in this document:
* The recommended option is to use the [Kubernetes Helm tool](https://github.com/helm/helm/blob/master/README.md), which can then also manage your deployment's lifecycle including upgrade and delete. To enable this using current Helm v2, Helm's server-side component Tiller must be installed in your Kubernetes environment with rights granted to manage deployments. There are best practices to secure Helm and Tiller and they need to be applied carefully if strict security is required e.g.: in a production environment.
* Another option is to generate a set of templates with customized values from the PubSub+ Helm chart and then use the Kubernetes native `kubectl` tool to deploy. The deployment will use the authorizations of the requesting user. However, in this case Helm will not be able to manage your Kubernetes rollouts lifecycle.

The next sections will provide details on the PubSub+ Helm chart, dependencies and customization options, followed by deployment prerequisites and the actual deployment steps.

## PubSub+ Helm Chart Deployment Considerations

The following diagram illustrates the template organization used for the PubSub+ Deployment chart. Note that the minimum is shown in this diagram to give you some background regarding the relationships and major functions.
![alt text](/docs/images/template_relationship.png "`pubsubplus` chart template relationship")

The StatefulSet template controls the pods of a PubSub+ deployment. It also mounts the scripts from the ConfigMap and the files from the Secrets, and maps PubSub+ data directories to a storage volume through a StorageClass, if configured. The Service template provides the event broker services at defined ports. The Service-Discovery template is only used internally so pods in a PubSub+ redundancy group can communicate with each-other in an HA setting.

All the `pubsubplus` chart parameters are documented in the [PubSub+ Helm Chart](/pubsubplus/README.md#configuration) reference.

### Deployment scaling

Solace PubSub+ event broker can be vertically scaled by deploying in one of the [client connection scaling tiers](//docs.solace.com/Configuring-and-Managing/SW-Broker-Specific-Config/Scaling-Tier-Resources.htm), controlled by the `solace.size` chart parameter.

Depending on the `solace.redundancy` parameter, one PubSub+ event router pod is deployed in a single-node Standalone deployment or three pods if deploying a [High-Availability (HA) group](//docs.solace.com/Overviews/SW-Broker-Redundancy-and-Fault-Tolerance.htm).

Horizontal scaling is possible through [connecting multiple deployments](//docs.solace.com/Overviews/DMR-Overview.htm).

### CPU and Memory Requirements

The following CPU and memory requirements (for each pod) are summarized here from the [Solace documentation](//docs.solace.com/Configuring-and-Managing/SW-Broker-Specific-Config/Scaling-Tier-Resources.htm#Cloud) for the possible `pubsubplus` chart `solace.size` parameter values:
* `dev`: no guaranteed performance, minimum requirements: 1 CPU, 1 GB memory
* `prod100`: up to 100 connections, minimum requirements: 2 CPU, 2 GB memory
* `prod1k`: up to 1,000 connections, minimum requirements: 2 CPU, 4 GB memory
* `prod10k`: up to 10,000 connections, minimum requirements: 4 CPU, 12 GB memory
* `prod100k`: up to 100,000 connections, minimum requirements: 8 CPU, 28 GB memory
* `prod200k`: up to 200,000 connections, minimum requirements: 12 CPU, 56 GB memory

### Disk Storage

The [PubSub+ deployment uses disk storage](//docs.solace.com/Configuring-and-Managing/Configuring-Storage.htm#Storage-) for logging, configuration, guaranteed messaging and other purposes, allocated from Kubernetes volumes.

Storage size (`storage.size` parameter) requirements for the scaling tiers:
* `dev`: no guaranteed performance: 5GB
* `prod100`: up to 100 connections, 7GB
* `prod1k`: up to 1,000 connections, 14GB
* `prod10k`: up to 10,000 connections, 18GB
* `prod100k`: up to 100,000 connections, 30GB
* `prod200k`: up to 200,000 connections, 34GB

The use of a persistent storage is recommended, otherwise if a pod-local storage is used data will be lost with the loss of a pod. The `storage.persistent` parameter is set to `true` by default.

The `pubsubplus` chart supports allocation of new storage volumes or mounting volumes with existing data. To avoid data corruption ensure to allocate clean new volumes for new deployments.

The recommended default allocation is to use Kubernetes [Storage Classes]((//kubernetes.io/docs/concepts/storage/storage-classes/) utilizing [Dynamic Volume Provisioning](//kubernetes.io/docs/concepts/storage/dynamic-provisioning/). The `pubsubplus` chart deployment will create a Persistent Volume Claim (PVC) specifying the size and the Storage Class of the requested volume and a Persistent Volume (PV) that meets the requirements will be allocated. Both the PVC and PV names will be linked to the deployment's name and when deleting PubSub+ pod(s) or even the entire deployment, the PVC and the allocated PV will not be deleted so potentially complex configuration is preserved. They will be re-mounted and reused with the existing configuration when a new pod starts (controlled by the StatefulSet, automatically matched to the old pod even in an HA deployment) or a deployment with the same as the old name is started. Explicitly delete a PVC if no longer needed, which will delete the corresponding PV - refer to [Deleting a Deployment](#deleting-a-deployment).

Instead of using a storage class, the `pubsubplus` chart also allows to describe how to assign storage by adding your own YAML fragment in the `storage.customVolumeMount` parameter. The fragment is inserted for the `data` volume in the `{spec.template.spec.volumes}` section of the ConfigMap. Note that in this case the `storage.useStorageClass` parameter is ignored.

Followings are examples of how to specify parameter values in common use cases:

#### Using the default or an existing storage class

Set the `storage.useStorageClass` parameter to use a particular storage class or leave this parameter to default undefined to allocate from your platform's "default" storage class - ensure it exists.
```bash
# Check existing storage classes
kubectl get storageclass
```
<br/>

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
<br/>

When using NFS, or generally if allocating from a defined Kubernetes [Persistent Volume](//kubernetes.io/docs/concepts/storage/persistent-volumes/#persistent-volumes), specify a `storageClassName` in the PV manifest as in this NFS example, then set the `storage.useStorageClass` parameter to the same:
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
Note: NFS is currently supported for development and demo purposes. If using NFS also set the `storage.slow` parameter to 'true'.
<br/>

#### Using an existing PVC

It is possible to use an existing PVC with its associated PV for storage, but it must be taken into account that the deployment will try to use any existing, potentially incompatible, configuration data on that volume.

Provide this custom YAML fragment in `storage.customVolumeMount`:

```yaml
  customVolumeMount: |
    persistentVolumeClaim:
      claimName: existing-pvc-name
```

#### Using a pre-created provider-specific volume

The PubSub+ Kubernetes deployment is expected to work with all [types of volumes](//kubernetes.io/docs/concepts/storage/volumes/#types-of-volumes ) your environment supports. In this case provide the specifics on mounting it in a custom YAML fragment in `storage.customVolumeMount`.

Following shows how to implement the [gcePersistentDisk example](//kubernetes.io/docs/concepts/storage/volumes/#gcepersistentdisk), note how the portion of the pod manifest example after `{spec.volumes.name}` is specified:
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

### Exposing the PubSub+ Event Broker Services

[PubSub+ event broker services](//docs.solace.com/Configuring-and-Managing/Default-Port-Numbers.htm#Software) can be exposed through one of the [Kubernetes service types](//kubernetes.io/docs/concepts/services-networking/service/#publishing-services-service-types) by specifying the `service.type` parameter:

* LoadBalancer - an external load balancer (default)
* NodePort
* ClusterIP

To support [Internal load balancers](//kubernetes.io/docs/concepts/services-networking/service/#internal-load-balancer), provider-specific service annotation may be added through defining the `service.annotations` parameter.

The `service.ports` parameter defines the services exposed. It specifies the event broker `containerPort` which actually provides the service, and the mapping to the `servicePort` at which the service can be accessed when using LoadBalancer or ClusterIP. Note that there is no control to which port services are mapped when using NodePort.

When using Helm to initiate a deployment, notes will be provided on the screen how to obtain the service addresses and ports specific to your deployment - follow the "Services access" section of the notes. 

A deployment is ready for service requests when there is a Solace pod that is running, `1/1` ready, and the pod's label is "active=true". The exposed `pubsubplus` service will forward traffic to that active message broker node. 

#### Using pod label "active" to identify the active event broker node

This section provides more information about what is required to achieve the correct label for the pod hosting the active event broker node.

Use `kubectl get pods --show-labels` to check for the status of the "active" label. In a stable deployment, one of the message routing nodes with ordinal 0 or 1 shall have the label `active=true`. You can find out if there is an issue by [checking events](#viewing-events) for related ERROR reported.

This label is set by the `readiness_check.sh` script in `pubsubplus/templates/solaceConfigMap.yaml`, triggered by the StatefulSet's readiness probe. For this to happen the followings are required:

- the Solace pods must be able to communicate with each-other at port 8080 and internal ports using the Service-Discovery service.
- the Kubernetes service account associated with the Solace pod must have sufficient rights to patch the pod's label when the active event broker is service ready
- the Solace pods must be able to communicate with the Kubernetes API at `kubernetes.default.svc.cluster.local` at port $KUBERNETES_SERVICE_PORT. You can find out the address and port by [SSH into the pod](#ssh-access-to-individual-message-brokers).

### Specifying the PubSub+ Docker image for the deployment

#### Source container registry

The `image.repository` and `image.tag` parameters specify the PubSub+ Docker image to be used for the deployment. They can either point to an image in a public or in a private Docker container registry.

The default parameters point to the latest release of the free PubSub+ Standard Edition from the [public Solace Docker Hub repo](//hub.docker.com/r/solace/solace-pubsub-standard/). It is generally recommended to set `image.tag` to a specific build for traceability purposes.

The following steps are applicable if using a private Docker container registry (e.g.: GCR, ECR or Harbor):
1. Get the Solace PubSub+ event broker Docker image tar.gz archive
2. Load the image into the private Docker registry 

To get the PubSub+ event broker Docker image URL, go to the Solace Developer Portal and download the Solace PubSub+ software event broker as a **docker** image or obtain your version from Solace Support.

| PubSub+ Standard<br/>Docker Image | PubSub+ Enterprise Evaluation Edition<br/>Docker Image
| :---: | :---: |
| Free, up to 1k simultaneous connections,<br/>up to 10k messages per second | 90-day trial version, unlimited |
| [Download Standard docker image](http://dev.solace.com/downloads/ ) | [Download Evaluation docker image](http://dev.solace.com/downloads#eval ) |

To load the Solace Docker image into a private Docker registry, follow the general steps below; for specifics, consult the documentation of the registry you are using.

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

Following additional step may be required if using signed images:

#### Using ImagePullSecrets for signed images

ImagePullSecrets may be required if using signed images from a private Docker registry, e.g.: Harbor.

Here is an example of creating an ImagePullSecret. Refer to your registry's documentation for the specific details of use.

```sh
kubectl create secret docker-registry <pull-secret-name> --dockerserver=<private-registry-server> \
  --docker-username=<registry-user-name> --docker-password=<registry-user-password> \
  --docker-email=<registry-user-email>
```

Then set the `image.pullSecretName` value to `<pull-secret-name>`.

### Security considerations

#### Privileged false

The PubSub+ container already runs in non-privileged mode.

#### Securing Helm 

Refer to [...]

#### Enabling pod label "active" in a tight security environment

Services require [pod label "active"](#using-pod-label-active-to-identify-the-active-event-broker-node) of the serving event broker.
* In a controlled environment it may be necessary to add a [NetworkPolicy](//kubernetes.io/docs/concepts/services-networking/network-policies/ ) to enable [required communication](#using-pod-label-active-to-identify-the-active-event-broker-node).
* The template [podModRbac.yaml](//github.com/SolaceProducts/solace-kubernetes-quickstart/blob/master/solace/templates/podModRbac.yaml )
is used to associate "patch label" rights. For simplicity, by default this opens up cluster-wide access of patching pod labels for all service accounts. For label update to work in a restricted security environment, adjust `podtagupdater` to be a `Role` and use a `RoleBinding` only to the specific service account in the specific namespace:

```yaml
kind: Role
apiVersion: rbac.authorization.k8s.io/v1
metadata:
  name: {{ template "solace.fullname" . }}-podtagupdater
rules:
- apiGroups: [""] # "" indicates the core API group
  resources: ["pods"]
  verbs: ["patch"]
---
kind: RoleBinding
apiVersion: rbac.authorization.k8s.io/v1beta1
metadata:
  name: {{ template "solace.fullname" . }}-serviceaccounts-to-podtagupdater
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: Role
  name: {{ template "solace.fullname" . }}-podtagupdater
subjects:
- kind: ServiceAccount
  name: <My-Service-Account>
  namespace: <My-Namespace>
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
* Minikube
* VMWare PKS

Check your platform running the `kubectl get nodes` command from your command-line client.

#### Install and setup the Helm package manager

The Solace PubSub+ event broker can be deployed using both Helm v2 (stable) and Helm v3 (about to be released). Most deployments currently use Helm v2.

If `helm version` fails on your command-line client then this may involve installing Helm and/or if using Helm v2 (default for now) then also deploying Tiller, its in-cluster operator.

1. Install the Helm client following [your platform-specific instructions](//helm.sh/docs/using_helm/#installing-the-helm-client ). For Linux, you can use:
```shell
curl -sSL https://raw.githubusercontent.com/helm/helm/master/scripts/get | bash
```

2. Deploy Tiller if using Helm v2 to manage your deployment. Following script is based on [the Example: Service account with cluster-admin role](//helm.sh/docs/using_helm/#example-service-account-with-cluster-admin-role ).

**Important:** this will grant Tiller `cluster-admin` privileges to enable getting started on most platforms. This should be more secured for Production environments and may already fail in a restricted security environment. For options, see section [Security considerations](#security-considerations).

```shell
kubectl -n kube-system create serviceaccount tiller
kubectl create clusterrolebinding tiller --clusterrole cluster-admin --serviceaccount=kube-system:tiller
helm init --wait --service-account=tiller  --upgrade
```

#### Restoring access to Helm

Follow the [instructions to install Helm](https://helm.sh/docs/using_helm/#installing-helm ) in your environment.

By default Tiller is deployed in a permissive configuration.

[Securing your Helm Installation](//helm.sh/docs/using_helm/#securing-your-helm-installation ) provides an overview of the Tiller-related security issues and recommended best practices.

Particularly, the [Role-based Access Control section of the Helm documentation](//helm.sh/docs/using_helm/#role-based-access-control) provides options that should be used in RBAC-enabled Kubernetes environments (v1.6+).

It is also possible to [**use Helm v2 as a templating engine only, with no Tiller deployed**](Ref to Solace HowTo), however Helm will not be able to manage your Kubernetes rollouts lifecycle.

#### Using Helm v3

The Helm 3 executable is available from https://github.com/helm/helm/releases. Installation of Tiller is no longer required. Ensure that your v3 installation does not conflict with an existing Helm v2 installation. Further (at this time draft) documentation is available from https://v3.helm.sh/.

### Persistent Storage

Ensure to have a way of assigning a storage volume to PubSub+ data directories, follow section [Disk Storage](#disk-storage).

## Deployment options

As discussed in the [Overview](#overview), two types of deployments will be described:
* Deployment steps using Helm, as package manager
* Alternative Deployment with generating templates for the Kubernetes `kubectl` tool

### Deployment steps using Helm

The recommended way is to make use of published pre-packaged PubSub+ charts from Solace' public repo with customizing your deployment through [available chart parameters](/pubsubplus/README.md).

Add or refresh a local Solace `solacecharts` repo:
```bash
# Add new
helm repo add solacecharts https://solacedev.github.io/solace-kubernetes-quickstart/helm-charts
# Refresh if needed, e.g.: to use a recently published chart version
helm repo update solacecharts
# Install from the repo
helm install solacecharts/pubsubplus
```

There are three Helm chart variants available from the repo with default small-size configurations:
1.	`pubsubplus-dev` - minimum footprint PubSub+ for Developers (Standalone)
2.	`pubsubplus` - PubSub+ Standalone, supporting 100 connections
3.	`pubsubplus-ha` - PubSub+ HA, supporting 100 connections

Refer to the [quick start](/README.md) for additional deployment details.

**More customization**

If more customization than just using Helm parameters is required, it is possible to create your own fork so templates can be edited:
```bash
# This creates a local directory with the published templates
helm fetch solacecharts/pubsubplus --untar
# Use the Helm chart from this directory
helm install ./pubsubplus
```
Note: it is encouraged to raise a [GitHub issue](https://github.com/SolaceProducts/solace-kubernetes-quickstart/issues/new) to possibly contribute your enhancements back to the project.

### Alternative Deployment with generating templates for the Kubernetes `kubectl` tool

This is for users not wishing to install the Helm server-side Tiller on the Kubernetes cluster.

This method will first generate installable Kubernetes templates from this project's Helm charts, then the templates can be installed using the Kubectl tool.

Note that later sections of this document about modifying, upgrading or deleting a Deployment using the Helm tool do not apply.

#### Step 1: Generate Kubernetes templates for Solace event broker deployment

1) Clone this project:

```sh
git clone https://github.com/SolaceProducts/solace-kubernetes-quickstart.git
cd solace-kubernetes-quickstart # This directory will be referenced as <project-root>
```

2) [Download](//github.com/helm/helm/releases/tag/v2.15.2 ) and install the Helm client locally.

We will assume that it has been installed to the `<project-root>/bin` directory.

3) Customize the Solace chart for your deployment

The Solace chart includes raw Kubernetes templates and a "values.yaml" file to customize them when the templates are generated.

The chart is located in the `solace` directory:

`cd <project-root>/solace`

a) Optionally replace the `<project-root>/solace/values.yaml` file with one of the prepared examples from the `<project-root>/solace/values-examples` directory. For details refer to the [Other Deployment Configurations section](#other-message-broker-deployment-configurations) in this document.

b) Then edit `<project-root>/solace/values.yaml` and replace following parameters:

SOLOS_CLOUD_PROVIDER: Current options are "gcp" or "aws" or leave it unchanged for unknown (note: specifying the provider will optimize volume provisioning for supported providers).
<br/>
SOLOS_IMAGE_REPO and SOLOS_IMAGE_TAG: use `solace/solace-pubsub-standard` and `latest` for the latest available or specify a [version from DockerHub](//hub.docker.com/r/solace/solace-pubsub-standard/tags/ ). For more options, refer to the [Solace PubSub+ event broker docker image section](#step-3-optional) in this document. 

c) Configure the Solace management password for `admin` user in `<project-root>/solace/templates/secret.yaml`:

SOLOS_ADMIN_PASSWORD: change it to the desired password, considering the [password rules](//docs.solace.com/Configuring-and-Managing/Configuring-Internal-CLI-User-Accounts.htm#Changing-CLI-User-Passwords ).

4) Generate the templates

```sh
cd <project-root>/solace
# Create location for the generated templates
mkdir generated-templates
# In next command replace myrelease to the desired release name
<project-root>/bin/helm template --name myrelease --values values.yaml --output-dir ./generated-templates .
```

The generated set of templates are now available in the `<project-root>/solace/generated-templates` directory.

#### Step 2: Deploy the templates on the target system

Assumptions: `kubectl` is deployed and configured to point to your Kubernetes cluster

1) Optionally copy the `generated-templates` directory with contents if this is on a different host

2) Assign rights to current user to modify cluster-wide RBAC (required for creating clusterrole binding when deploying the Solace template podModRbac.yaml)

Example:

```sh
# Get current user - GCP example. Returns e.g.: myname@example.org
gcloud info | grep Account  
# Assign rigths - replace user
kubectl create clusterrolebinding myname-cluster-admin-binding \
  --clusterrole=cluster-admin \
  --user=myname@example.org
```

3) Initiate the deployment:

`kubectl apply --recursive -f ./generated-templates/solace`

Wait for the deployment to complete, which is then ready to use.

4) To delete the deployment, execute:

`kubectl delete --recursive -f ./generated-templates/solace`



## Validating the Deployment

Now you can validate your deployment on the command line. In this example an HA configuration is deployed with pod/XXX-XXX-solace-0 being the active message broker/pod. The notation XXX-XXX is used for the unique release name that Helm dynamically generates, e.g: "tinseled-lamb".

```sh
prompt:~$ kubectl get statefulsets,services,pods,pvc,pv
NAME                                 DESIRED   CURRENT   AGE
statefulsets/XXX-XXX-solace   3         3         3m
NAME                                  TYPE           CLUSTER-IP      EXTERNAL-IP      PORT(S)                                       AGE
svc/XXX-XXX-solace             LoadBalancer   10.15.249.186   35.202.131.158   22:32656/TCP,8080:32394/TCP,55555:31766/TCP   3m
svc/XXX-XXX-solace-discovery   ClusterIP      None            <none>           8080/TCP                                      3m
svc/kubernetes                        ClusterIP      10.15.240.1     <none>           443/TCP                                       6d
NAME                         READY     STATUS    RESTARTS   AGE
po/XXX-XXX-solace-0   1/1       Running   0          3m
po/XXX-XXX-solace-1   1/1       Running   0          3m
po/XXX-XXX-solace-2   1/1       Running   0          3m
NAME                               STATUS    VOLUME                                     CAPACITY   ACCESS MODES   STORAGECLASS              AGE
pvc/data-XXX-XXX-solace-0   Bound     pvc-74d9ceb3-d492-11e7-b95e-42010a800173   30Gi       RWO            XXX-XXX-standard   3m
pvc/data-XXX-XXX-solace-1   Bound     pvc-74dce76f-d492-11e7-b95e-42010a800173   30Gi       RWO            XXX-XXX-standard   3m
pvc/data-XXX-XXX-solace-2   Bound     pvc-74e12b36-d492-11e7-b95e-42010a800173   30Gi       RWO            XXX-XXX-standard   3m
NAME                                          CAPACITY   ACCESS MODES   RECLAIM POLICY   STATUS    CLAIM                                  STORAGECLASS              REASON    AGE
pv/pvc-74d9ceb3-d492-11e7-b95e-42010a800173   30Gi       RWO            Delete           Bound     default/data-XXX-XXX-solace-0   XXX-XXX-standard             3m
pv/pvc-74dce76f-d492-11e7-b95e-42010a800173   30Gi       RWO            Delete           Bound     default/data-XXX-XXX-solace-1   XXX-XXX-standard             3m
pv/pvc-74e12b36-d492-11e7-b95e-42010a800173   30Gi       RWO            Delete           Bound     default/data-XXX-XXX-solace-2   XXX-XXX-standard             3m


prompt:~$ kubectl describe service XXX-XX-solace
Name:                     XXX-XXX-solace
Namespace:                default
Labels:                   app=solace
                          chart=solace-0.3.0
                          heritage=Tiller
                          release=XXX-XXX
Annotations:              <none>
Selector:                 active=true,app=solace,release=XXX-XXX
Type:                     LoadBalancer
IP:                       10.55.246.5
LoadBalancer Ingress:     35.202.131.158
Port:                     ssh  22/TCP
TargetPort:               2222/TCP
NodePort:                 ssh  30828/TCP
Endpoints:                10.52.2.6:2222
:
:
```

Generally, all services including management and messaging are accessible through a Load Balancer. In the above example `35.202.131.158` is the Load Balancer's external Public IP to use.

> Note: When using MiniKube, there is no integrated Load Balancer. For a workaround, execute `minikube service XXX-XXX-solace` to expose the services. Services will be accessible directly using mapped ports instead of direct port access, for which the mapping can be obtained from `kubectl describe service XXX-XX-solace`.

### Gaining admin access to the message broker

Refer to the [Management Tools section](//docs.solace.com/Management-Tools.htm ) of the online documentation to learn more about the available tools. The WebUI is the recommended simplest way to administer the message broker for common tasks.

#### WebUI, SolAdmin and SEMP access

Use the Load Balancer's external Public IP at port 8080 to access these services.

#### Solace CLI access

If you are using a single message broker and are used to working with a CLI message broker console access, you can SSH into the message broker as the `admin` user using the Load Balancer's external Public IP:

```sh

$ssh -p 22 admin@35.202.131.158
Solace PubSub+ Standard
Password:

Solace PubSub+ Standard Version 8.10.0.1057

The Solace PubSub+ Standard is proprietary software of
Solace Corporation. By accessing the Solace PubSub+ Standard
you are agreeing to the license terms and conditions located at
//www.solace.com/license-software

Copyright 2004-2018 Solace Corporation. All rights reserved.

To purchase product support, please contact Solace at:
//dev.solace.com/contact-us/

Operating Mode: Message Routing Node

XXX-XXX-solace-0>
```

If you are using an HA deployment, it is better to access the CLI through the Kubernets pod and not directly via SSH.

Note: SSH access to the pod has been configured at port 2222. For external access SSH has been configured to to be exposed at port 22 by the load balancer.

* Loopback to SSH directly on the pod

```sh
kubectl exec -it XXX-XXX-solace-0  -- bash -c "ssh -p 2222 admin@localhost"
```

* Loopback to SSH on your host with a port-forward map

```sh
kubectl port-forward XXX-XXX-solace-0 62222:2222 &
ssh -p 62222 admin@localhost
```

This can also be mapped to individual message brokers in the deployment via port-forward:

```
kubectl port-forward XXX-XXX-solace-0 8081:8080 &
kubectl port-forward XXX-XXX-solace-1 8082:8080 &
kubectl port-forward XXX-XXX-solace-2 8083:8080 &
```

#### SSH access to individual message brokers

For direct access, use:

```sh
kubectl exec -it XXX-XXX-solace-<pod-ordinal> -- bash
```

### Testing data access to the message broker

To test data traffic though the newly created message broker instance, visit the Solace Developer Portal and and select your preferred programming language in [send and receive messages](//dev.solace.com/get-started/send-receive-messages/). Under each language there is a Publish/Subscribe tutorial that will help you get started and provide the specific default port to use.

Use the external Public IP to access the deployment. If a port required for a protocol is not opened, refer to the next section on how to open it up.

## Troubleshooting

### Viewing logs

Logs from the currently running container:

```sh
kubectl logs XXX-XXX-solace-0 -c solace  # use -f to follow live
```

Logs from the previously terminated container:

```sh
kubectl logs XXX-XXX-solace-0 -c solace -p
```

### Viewing events

Kubernetes collects [all events for a cluster in one pool](//kubernetes.io/docs/tasks/debug-application-cluster/events-stackdriver ). This includes events related to the Solace message broker deployment.

It is recommeded to watch events when creating or upgrading a Solace deployment. Events clear after about an hour. You can query all available events:

```sh
kubectl get events  # use -w to watch live
```

### Solace event broker troubleshooting

#### General troubleshooting hints
https://kubernetes.io/docs/tasks/debug-application-cluster/debug-application/

#### Pods stuck not enough resources

-> Increase K8S resources

#### Pods stuck no storage

=> have a storage or use ephemeral (not for Production!)

#### Pods stuck in CrashLoopBackoff or Failed

=> increase the Liveliness probe timeout and retry

#### Security constraints

=> ensure adequate RBAC for your roles
=> open up network access to the k8s aAPI



## Modifying or upgrading a Deployment

To upgrade/modify the message broker deployment, make the required modifications to the chart in the `solace-kubernetes-quickstart/solace` directory as described next, then run the Helm tool from here. When passing multiple `-f <values-file>` to Helm, the override priority will be given to the last (right-most) file specified.

To **upgrade** the version of the message broker running within a Kubernetes cluster:

- Add the new version of the message broker to your container registry.
- Create a simple upgrade.yaml file in solace-kubernetes-quickstart/solace directory, e.g.:

```sh
image:
  repository: <repo>/<project>/solace-pubsub-standard
  tag: NEW.VERSION.XXXXX
  pullPolicy: IfNotPresent
```
- Upgrade the Kubernetes release.

Note: upgrade will begin immediately, in the order of pod 2, 1 and 0 (Monitor, Backup, Primary) taken down for upgrade in an HA deployment. This will affect running message broker instances, result in potentially multiple failovers and requires connection retries configured in the client.

```sh
cd ~/workspace/solace-kubernetes-quickstart/solace
helm upgrade XXX-XXX . -f values.yaml -f upgrade.yaml
```


Similarly, to **modify** other deployment parameters, e.g. to change the ports exposed via the loadbalancer, you need to upgrade the release with a new set of ports. In this example we will add the MQTT 1883 tcp port to the loadbalancer.

```
cd ~/workspace/solace-kubernetes-quickstart/solace
tee ./port-update.yaml <<-EOF   # create update file with following contents:
service:
  internal: false
  type: LoadBalancer
  externalPort:
    - port: 1883
      protocol: TCP
      name: mqtt
      targetport: 1883
    - port: 22
      protocol: TCP
      name: ssh
      targetport: 2222
    - port: 8080
      protocol: TCP
      name: semp
    - port: 55555
      protocol: TCP
      name: smf
    - port: 943
      protocol: TCP
      name: semptls
      targetport: 60943
    - port: 80
      protocol: TCP
      name: web
      targetport: 60080
    - port: 443
      protocol: TCP
      name: webtls
      targetport: 60443
  internalPort:
    - port: 2222
      protocol: TCP
    - port: 8080
      protocol: TCP
    - port: 55555
      protocol: TCP
    - port: 60943
      protocol: TCP
    - port: 60080
      protocol: TCP
    - port: 60443
      protocol: TCP
    - port: 1883
      protocol: TCP
EOF
helm upgrade  XXXX-XXXX . --values values.yaml --values port-update.yaml
```


## Deleting a Deployment

Use Helm to delete a deployment, also called a release:

```
helm delete XXX-XXX
```

Check what has remained from the deployment, which should only return a single line with svc/kubernetes:

```
kubectl get statefulsets,services,pods,pvc,pv
NAME                           TYPE           CLUSTER-IP      EXTERNAL-IP       PORT(S)         AGE
service/kubernetes             ClusterIP      XX.XX.XX.XX     <none>            443/TCP         XX
```

> Note: Helm will not clean up all the deployment artifacts, e.g.: pvc/ and pv/. Use `kubectl delete` to delete those.

## Additional notes







