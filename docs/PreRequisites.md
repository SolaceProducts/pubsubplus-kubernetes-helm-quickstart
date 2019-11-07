# Pre-requisites for the Solace PubSub+ Deployment

Overview:
  * [Perform any necessary platform-specific setup](#perform-any-necessary-platform-specific-setup)
  * [Install the `kubectl` command-line tool](#install-the--kubectl--command-line-tool)
  * [Install and setup the Helm package manager](#install-and-setup-the-helm-package-manager)
  * [Load the PubSub+ Docker image to a private Docker image registry](#load-the-solace-docker-image-to-a-private-docker-image-registry)
  
## Perform any necessary platform-specific setup

- Amazon EKS
- Azure AKS
- GCP
- OpenShift
- Minikube
- VMWare PKS

## Install the `kubectl` command-line tool

Refer to [these instructions](//kubernetes.io/docs/tasks/tools/install-kubectl/) to install `kubectl` if your Kubernetes platform does not already provide this tool or equivalent (like `oc` in OpenShift).

## Install and setup the Helm package manager

The Solace PubSub+ event broker can be deployed using both Helm v2 (stable) and Helm v3 (about to be released). Most deployments currently use Helm v2.

If `helm version` fails on your command-line client then this involves installing Helm and if using Helm v2 (default for now) then also deploying Tiller, its in-cluster operator.

1. Install the Helm client following [your platform-specific instructions](//helm.sh/docs/using_helm/#installing-the-helm-client ). For Linux, you can use:
```shell
export DESIRED_VERSION=v2.15.2
curl -sSL https://raw.githubusercontent.com/helm/helm/master/scripts/get | bash
```

2. Deploy Tiller. Following script is based on [the Example: Service account with cluster-admin role](//helm.sh/docs/using_helm/#example-service-account-with-cluster-admin-role ).

**Important:** this will grant Tiller `cluster-admin` privileges to enable getting started on most platforms. This should be more secured for Production environments and may already fail in a restricted security environment. For options, see section [Security considerations](#security-considerations).

```shell
kubectl -n kube-system create serviceaccount tiller
kubectl create clusterrolebinding tiller --clusterrole cluster-admin --serviceaccount=kube-system:tiller
helm init --wait --service-account=tiller  --upgrade
```

### Installing Helm v2

Follow the [instructions to install Helm](https://helm.sh/docs/using_helm/#installing-helm ) in your environment.

### Security considerations

By default Tiller is deployed in a permissive configuration.

[Securing your Helm Installation](//helm.sh/docs/using_helm/#securing-your-helm-installation ) provides an overview of the Tiller-related security issues and recommended best practices.

Particularly, the [Role-based Access Control section of the Helm documentation](//helm.sh/docs/using_helm/#role-based-access-control) provides options that should be used in RBAC-enabled Kubernetes environments (v1.6+).

It is also possible to [**use Helm v2 as a templating engine only, with no Tiller deployed**](Ref to Solace HowTo), however Helm will not be able to manage your Kubernetes rollouts lifecycle.

### Using Helm v3

The Helm 3 executable is available at https://github.com/helm/helm/releases. Installation of Tiller is no longer required. Ensure that your v3 installation does not conflict with an existing Helm v2 installation. Further (at this time draft) documentation is available from https://v3.helm.sh/.

## Load the PubSub+ Docker image to a private Docker image registry

**Hint:** You may skip the rest of this step if not using a private Docker image registry (e.g.: GCR, ECR or Harbor). The free PubSub+ Standard Edition is available from the [public Docker Hub registry](//hub.docker.com/r/solace/solace-pubsub-standard/tags/ ), the image reference is `solace/solace-pubsub-standard:<TagName>`.

To get the PubSub+ event broker Docker image URL, go to the Solace Developer Portal and download the Solace PubSub+ software event broker as a **docker** image or obtain your version from Solace Support.

| PubSub+ Standard<br/>Docker Image | PubSub+ Enterprise Evaluation Edition<br/>Docker Image
| :---: | :---: |
| Free, up to 1k simultaneous connections,<br/>up to 10k messages per second | 90-day trial version, unlimited |
| [Download Standard docker image](http://dev.solace.com/downloads/ ) | [Download Evaluation docker image](http://dev.solace.com/downloads#eval ) |

To load the Solace Docker image into other private Docker registry, follow the general steps below; for specifics, consult the documentation of the registry you are using.

* Prerequisite: local installation of [Docker](//docs.docker.com/get-started/ ) is required
* First load the image to the local docker registry:
```sh
# Option a): If you have a local tar.gz Docker image file
sudo docker load -i <solace-pubsub-XYZ-docker>.tar.gz
# Option b): You can use the public Solace Docker image from Docker Hub
sudo docker pull solace/solace-pubsub-standard:latest # or specific <TagName>

# Verify the image has been loaded and note the associated "IMAGE ID"
sudo docker images
```
* Login to the private registry:
```sh
sudo docker login <private-registry> ...
```
* Tag the image with the desired name and tag:
```sh
sudo docker tag <image-id> <private-registry>/<path>/<image-name>:<tag>
```
* Push the image to the private registry
```sh
sudo docker push <private-registry>/<path>/<image-name>:<tag>
```

Note that additional steps may be required if using signed images.

## Create and use ImagePullSecrets for signed images

ImagePullSecrets may be required if using signed images from a private Docker registry, e.g.: Harbor.

Here is an example of creating an ImagePullSecret. Refer to your registry's documentation for the specific details of use.

```sh
kubectl create secret docker-registry <pull-secret-name> --dockerserver=<private-registry-server> \
  --docker-username=<registry-user-name> --docker-password=<registry-user-password> \
  --docker-email=<registry-user-email>
```

Then set the `image.pullSecretName` value to `<pull-secret-name>`.

## Ensure a StorageClass is available

The Solace deployment uses disk storage for logging, configuration, guaranteed messaging and other purposes. The use of a persistent storage is recommended, otherwise if a pod-local storage is used data will be lost with the loss of a pod.

A [StorageClass](https://kubernetes.io/docs/concepts/storage/storage-classes/ ) is used to obtain a persistent storage that is external to the pod.

For a list of of available StorageClasses, execute
```sh
kubectl get storageclass
```

It is expected that there is at least one StorageClass available. By default the `pubsubplus` chart is configured to use the default StorageClass in your environment, adjust the `storage.useStorageClass` value if necessary.

Refer to your Kubernetes environment's documentation if a StorageClass needs to be created or to understand the differences if there are multiple options.

