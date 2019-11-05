# Pre-requisites for the Solace PubSub+ Deployment

  * [Perform any necessary platform-specific setup](#perform-any-necessary-platform-specific-setup)
  * [Setup Helm package manager](#setup-helm-package-manager)
    + [TL;DR;](#tl-dr-)
    + [Introduction](#introduction)
    + [Installing Helm v2](#installing-helm-v2)
    + [Securing Helm and Tiller](#securing-helm-and-tiller)
    + [Using Helm](#using-helm)
    + [Helm upgrade and rollback](#helm-upgrade-and-rollback)
    + [Helm delete](#helm-delete)
    + [Using Helm v3](#using-helm-v3)

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

### TL;DR;

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
helm init --service-account=tiller  --upgrade
kubectl rollout status -w deployment/tiller-deploy
```

### Installing Helm v2

Follow the [instructions to install Helm](https://helm.sh/docs/using_helm/#installing-helm ) in your environment.

### Security considerations

By default Tiller is deployed in a permissive configuration.

[Securing your Helm Installation](//helm.sh/docs/using_helm/#securing-your-helm-installation ) provides an overview of the Tiller-related security issues and recommended best practices.

Particularly, the [Role-based Access Control section of the Helm documentation](//helm.sh/docs/using_helm/#role-based-access-control) provides options that should be used in RBAC-enabled Kubernetes environments (v1.6+).

**Update Link**
It is also possible to [use Helm v2 as a templating engine only, with no Tiller deployed](Ref to Solace HowTo), however Helm will not be able to manage your Kubernetes rollouts lifecycle.

### Using Helm v3

The Helm 3 executable is available at https://github.com/helm/helm/releases. Installation of Tiller is no longer required. Ensure that your v3 installation does not conflict with an existing Helm v2 installation. Further (at this time draft) documentation is available from https://v3.helm.sh/.