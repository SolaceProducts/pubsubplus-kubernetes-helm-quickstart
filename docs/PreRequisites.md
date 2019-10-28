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

- GCP
- Amazon EKS
- Azure AKS
- OpenShift
- Minikube

## Install the `kubectl` command-line tool

Refer to [these instructions](//kubernetes.io/docs/tasks/tools/install-kubectl/) to install `kubectl` if your Kubernetes platform does not already provide this tool or equivalent (like `oc` in OpenShift).

## Install and setup the Helm package manager

This involves installing Helm on your command-line client and if using Helm v2 (default for now) deploying Tiller, its in-cluster operator.

### TL;DR;

1. Install the Helm client following [your platform-specific instructions](//helm.sh/docs/using_helm/#installing-the-helm-client ). For Linux, you can use:
```shell
export DESIRED_VERSION=v2.14.3
curl -sSL https://raw.githubusercontent.com/helm/helm/master/scripts/get | bash
```

2. Deploy Tiller by creating a cluster-admin role and initializing Helm following [the Example: Service account with cluster-admin role](//helm.sh/docs/using_helm/#example-service-account-with-cluster-admin-role ). (Use the provided content to create a `rbac-config.yaml` file then execute the commands below)<br/><br/>
**Important:** this will grant Tiller `cluster-admin` privileges to enable getting started on most platforms. This should be secured for Production environments, see section [Securing Helm and Tiller](#securing-helm-and-tiller).


### Introduction

The Solace PubSub+ event broker can be deployed using both Helm v2 (stable) and Helm v3 (about to be released). Most deployments currently use Helm v2.

### Installing Helm v2

Follow the [instructions to install Helm](https://helm.sh/docs/using_helm/#installing-helm ) in your environment.

### Security considerations

By default Tiller is deployed in a permissive configuration.

[Securing your Helm Installation](//helm.sh/docs/using_helm/#securing-your-helm-installation ) provides an overview of the Tiller-related security issues and recommended best practices.

Particularly, the [Role-based Access Control section of the Helm documentation](//helm.sh/docs/using_helm/#role-based-access-control) provides options that should be used in recent RBAC-enabled Kubernetes environments (v1.6+).

**Update Link**
It is also possible to [use Helm v2 as a templating engine only, with no Tiller deployed](Ref to Solace HowTo), however Helm will not be able to manage your Kubernetes rollouts lifecycle.

### Using Helm v3

The Helm 3 executable is available at https://github.com/helm/helm/releases. Installation of Tiller is no longer required. Ensure that your v3 installation does not conflict with an existing Helm v2 installation. Further (at this time draft) documentation is available from https://v3.helm.sh/.