# Solace PubSub+ Advanced Event Broker Helm Chart

The [Solace PubSub+ Platform](https://solace.com/products/platform/)'s [Advanced Event Broker](https://solace.com/products/event-broker/) efficiently streams event-driven information between applications, IoT devices and user interfaces running in cloud, on-premise, and hybrid environments using open APIs and protocols like AMQP, JMS, MQTT, REST and WebSocket. It can be installed into a variety of public and private clouds, PaaS, and on-premise environments, and brokers in multiple locations can be linked together in an [Event Mesh](https://solace.com/what-is-an-event-mesh/) to dynamically share events across the distributed enterprise.

## TL;DR;

```bash
helm repo add solacecharts https://solacedev.github.io/solace-kubernetes-quickstart/helm-charts
helm install --name my-release solacecharts/pubsubplus
```

## Overview

This chart bootstraps a single-node or HA deployment of a [Solace PubSub+ software event broker](https://solace.com/products/event-broker/software/) on a [Kubernetes](http://kubernetes.io) cluster using the [Helm](https://helm.sh) package manager.

The [Solace PubSub+ quickstart documentation](https://github.com/SolaceDev/solace-kubernetes-quickstart/blob/HelmReorg/README.md) provides additional details to this Helm chart.

## Prerequisites

* Kubernetes 1.9 or later
* Helm package manager installed and configured
* If using a private Docker registry, load the PubSub+ Docker image and for signed images create an image pull secret
* With persistent storage enabled (see [configuration](#configuration)):
  * Specify a storage class unless using a default storage class in your Kubernetes cluster
  
## Create a deployment

```bash
helm install --name my-release \
  --set solace.redundancy=true,solace.usernameAdminPassword=secretpassword <solace-chart-location>
```

## Delete a deployment

```bash
helm delete --purge my-release
kubectl get pvc | grep my-release
# Delete any PVCs reated to my-release
```



## Configuration

The following table lists the configurable parameters of the Solace chart and their default values.

Override default values using the `--set key=value[,key=value]` argument to `helm install`. For example,

For more ways to override default values, refer to [Customizing the Chart Before Installing](//helm.sh/docs/using_helm/#customizing-the-chart-before-installing).

| Parameter                      | Description                                                                                             | Default                                                 |
| ------------------------------ | ------------------------------------------------------------------------------------------------------- | ------------------------------------------------------- |
| `solace.redundancy`            | `false` will create a single-node non-HA deployment; `true` will create an HA deployment with Primary, Backup and Monitor nodes | `false` |
| `solace.size`                  | Connection scaling. Options: `dev` (requires minimum resources but no guaranteed performance), `prod100`, `prod1k`, `prod10k`, `prod100k`, `prod200k` | `prod100` | `prod100` |
| `solace.usernameAdminPassword` | The password for the "admin" management user. Will autogenerate it if not provided. **Important:** refer to the #documentation# how to retrieve it and use it for `helm upgrade`. | Autogenerate |
| `image.repository`             | The docker repo name and path to the Solace Docker image                                                | `solace/solace-pubsub-standard` from public DockerHub   |
| `image.tag`                    | The Solace Docker image tag. It is recommended to specify an explicit tag for production use            | `latest`                                                |
| `image.pullPolicy`             | Image pull policy                                                                                       | `IfNotPresent`                                          |
| `image.pullSecretName`         | Name of the ImagePullSecret to be used with the Docker registry                                         | not set, meaning no ImagePullSecret used                |
| `service.type`                 | How to expose the service: options include ClusterIP, NodePort, LoadBalancer                            | `LoadBalancer`                                          |
| `service.addExternalPort`      | Use to define additional Solace service ports exposed externally, with mapping to pod targetport        | not set                                                 |
| `service.addInternalPort`      | For any matching targetport in 'service.addExternalPort', this property will expose that port at the pod-level first | not set                                    |
| `storage.persistent`           | `false` to use ephemeral storage at pod level; `true` to request persistent storage through a StorageClass | `true`, false is not recommended for production use  |
| `storage.useStorageClass`      | Name of the StorageClass to be used to request persistent storage volumes                               | the default StorageClass for the Kubernetes cluster |
| `storage.size`                 | Size of the persistent storage to be used; Refer to the Solace documentation for storage configuration requirements | `30Gi` |


