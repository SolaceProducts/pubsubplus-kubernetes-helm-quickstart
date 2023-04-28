# "solace-pod-modifier" Admission Plugin

This project provides an [admission plugin](https://kubernetes.io/docs/reference/access-authn-authz/extensible-admission-controllers/) extension to Kubernetes v1.16 or later, to support reducing the resource requirements of PubSub+ Monitoring Nodes in an HA deployment.

Contents:
  * [Overview](#overview)
  * [Security considerations](#security-considerations)
  * [Building and Deployment](#building-and-deployment)
    + [Project structure](#project-structure)
    + [Tool pre-requisites](#tool-pre-requisites)
    + [Build and deploy steps](#build-and-deploy-steps)
  * [How to use](#how-to-use)
  * [Troubleshooting](#troubleshooting)

## Overview

"solace-pod-modifier" implements a web server acting as a ["MutatingAdmissionWebhook" admission controller](https://kubernetes.io/docs/reference/access-authn-authz/admission-controllers/). Support for both building and deployment is provided. 

When deployed it can intercept Pod create requests in enabled namespaces and can alter resource specifications of designated Pods before they are persisted.

This project is a fork of https://github.com/morvencao/kube-sidecar-injector, which may be consulted for additional details.

## Security considerations

Admission plugins intercepting Kubernetes API requests introduce inherent security risks of making unintended modifications.
Following safeguards are in place:
- The webhook is deployed in a dedicated namespace, only cluster level Kubernetes admins have access to that
- Webhook integrity: the webhook is packaged as a container image and a private repo can be used to serve it
- The webhook code ensures:
  * Only the "resources" of a pod can be modified, no other specs
  * Only pods in specified namespaces can be modified - namespaces must be labelled `pod-modifier.solace.com=enabled`
  * Only pods with annotation `pod-modifier.solace.com/modify: "true"` can be modified
  * Only pods with name that meets the specified name in `pod-modifier.solace.com/modify.podDefinition` annotation : `{"Pods":[{"metadata":{"name":"<pod-name>"}...` can be modified

## Building and Deployment

This project needs to be built first, which results in a container image of the webhook server in a specified repo. When deploying, a webhook pod will be created using the container image, a webhook service as an entry point for admission requests, and a `MutatingWebhookConfiguration` object, which is an Admission registration that specifies which webhook service to call and when.

> Note: this release only supports one replica of the webhook pod running, more replicas will be supported in a later release.

### Project structure

The server is implemented as a Go language project in the `cmd` subdirectory:
* `cmd/main.go`: entry point;
* `cmd/webhook.go`: implements the mutating logic;
* `cmd/cert.go`: creates a certificate to be used by admission requests from the Kubernetes controller and also gets it signed by the Kubernetes local CA. This is required at the Admission registration;
* `cmd/webhookconfig`: creates an Admission registration.

The Kubernetes deployment templates are provided in the `deploy` subdirectory:
* `deploy/kustomization.yaml`: provides base configuration to be used by the Kustomize tool. "Kustomize" is a Kubernetes tool used to override template settings;
* `deploy/deployment.yaml`: creates the webhook pod from the webhook server container image;
* `deploy/service.yaml`: defines the webhook service pointing to the webhook pod;
* `deploy/namespace.yaml`, `serviceaccount.yaml`, `clusterrole.yaml` and `clusterrolebinding.yaml` define a dedicated namespace and security settings for the deployment.

`Dockerfile` provides the template to build the container image.

`Makefile` defines the tasks related to building and deployment. Check `make help` for options.

### Tool pre-requisites

- [make](https://www.gnu.org/software/make/)
- [git](https://git-scm.com/downloads)
- [go](https://golang.org/dl/) version v1.17+
- [docker](https://docs.docker.com/install/) version 19.03+, or [podman](https://podman.io/getting-started/installation)
- [kubectl](https://kubernetes.io/docs/tasks/tools/install-kubectl/) version v1.19+
- Access to the target Kubernetes v1.16+ cluster with the `admissionregistration.k8s.io/v1` API enabled. Verify that by the following command: `kubectl api-versions | grep admissionregistration.k8s.io
`

### Build and deploy steps

1. Clone this project to your local machine

```
git clone https://github.com/SolaceProducts/pubsubplus-kubernetes-helm-quickstart.git
cd pubsubplus-kubernetes-helm-quickstart/solace-pod-modifier-admission-plugin
```

2. Build and push container image:

Decide in which image repo to host the built webhook container image, ensure write access to the repo, then substitute `<repo-name>`, `<image-name>` and `<tag>`:
```bash
make image-build image-push IMAGE=<repo-name>/<image-name>:<tag>
```

> **Important**: the image is based on `alpine:latest`. It is the builder's responsibility to keep updating the image for security patches etc. over time.

3. Deploy the `solace-pod-modifier` to the Kubernetes cluster:

```bash
make deploy IMAGE=<repo-name>/<image-name>:<tag>
```

Deployment options:
* Container image: as above, the container image is directly provided in the `make` command
* Image pull secrets: if required, uncomment and edit in `deploy/deployment.yaml`
* Namespace name: default is `solace-pod-modifier`, adjust in `deploy/kustomization.yaml`. *Important:* if using OpenShift, do not use the `default` namespace (project).

4. Verify the webhook pod is up and running in the `solace-pod-modifier` namespace and the `MutatingWebhookConfiguration` object has been created:

```bash
kubectl get pods -n solace-pod-modifier
NAME                                              READY   STATUS    RESTARTS   AGE
pod-modifier-webhook-deployment-d45f8b7dd-968gf   1/1     Running   0          30s

kubectl get MutatingWebhookConfiguration
NAME                               WEBHOOKS   AGE
...
pod-modifier.solace.com            1          36s
```

## How to use

With `solace-pod-modifier` [deployed](#build-and-deploy-steps),

1. Label the namespace designated for PubSub+ HA deployment with `pod-modifier.solace.com=enabled`:

```
kubectl create ns test-ns
kubectl label namespace test-ns pod-modifier.solace.com=enabled
# kubectl get namespace -L pod-modifier.solace.com
NAME                 STATUS   AGE   POD-MODIFIER.SOLACE.COM
default              Active   26m
test-ns              Active   13s   enabled
kube-public          Active   26m
kube-system          Active   26m
solace-pod-modifier  Active   17m
```

2. Deploy PubSub+ HA

```bash
helm install my-ha-deployment solacecharts/pubsubplus \
    --namespace test-ns \
    --set solace.redundancy=true,solace.podModifierEnabled=true
```

3. Verify Monitoring node (ordinal: `-2`) CPU or memory resource requirements

```
kubectl get pods -n test-ns -o yaml | grep "pod-name\:\|memory\:"
      statefulset.kubernetes.io/pod-name: my-ha-deployment-pubsubplus-0
          memory: 3410Mi
          memory: 3410Mi
      statefulset.kubernetes.io/pod-name: my-ha-deployment-pubsubplus-1
          memory: 3410Mi
          memory: 3410Mi
      statefulset.kubernetes.io/pod-name: my-ha-deployment-pubsubplus-2
          memory: 1965Mi
          memory: 1965Mi
```

## Troubleshooting

If the Monitoring node specs were not reduced, check followings:

1. The webhook pod is in running state and no error in the logs:
```
kubectl logs pod-modifier-webhook-deployment-d45f8b7dd-968gf -n solace-pod-modifier
```

2. The namespace in which the PubSub+ HA broker is deployed has the correct label (`pod-modifier.solace.com=enabled`) as configured in `MutatingWebhookConfiguration`.

3. Check if the broker pods have both annotations
* `pod-modifier.solace.com/inject: "true"`; and also
* `pod-modifier.solace.com/modify.podDefinition: ...`

4. Error message at Helm install or upgrade

Generally, if encountered an error message about "failed calling webhook" at Helm install or upgrade then delete or rollback the Helm deployment just attempted without deleting related PVCs. Check above items are all in place and then retry it. 


