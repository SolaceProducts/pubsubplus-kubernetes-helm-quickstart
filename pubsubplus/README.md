# Solace PubSub+ Advanced Event Broker Helm Chart

The [Solace PubSub+ Platform](https://solace.com/products/platform/)'s [PubSub+ Advanced Event Broker](https://solace.com/products/event-broker/) efficiently streams event-driven information between applications, IoT devices and user interfaces running in cloud, on-premise, and hybrid environments using open APIs and protocols like AMQP, JMS, MQTT, REST and WebSocket. It can be installed into a variety of public and private clouds, PaaS, and on-premise environments, and brokers in multiple locations can be linked together in an [Event Mesh](https://solace.com/what-is-an-event-mesh/) to dynamically share events across the distributed enterprise.

## Overview

This chart bootstraps a single-node or HA deployment of a [Solace PubSub+ software event broker](https://solace.com/products/event-broker/software/) on a [Kubernetes](http://kubernetes.io) cluster using the [Helm](https://helm.sh) package manager.

Additional documentation is available from the [Solace PubSub+ Event Broker on Kubernetes Deployment Guide](//github.com/SolaceDev/solace-kubernetes-quickstart/blob/HelmReorg/docs/PubSubPlusK8SDeployment.md).

## Prerequisites

* Kubernetes 1.9 or later platform with adequate [CPU and memory](/docs/PubSubPlusK8SDeployment.md#cpu-and-memory-requirements) and [storage resources](/docs/PubSubPlusK8SDeployment.md#disk-storage) for the targeted scaling tier requirements
* Helm package manager installed and configured with Tiller deployed if using Helm v2
* If using a private Docker registry, load the PubSub+ Docker image and for signed images create an image pull secret
* With persistent storage enabled (see in [Configuration](#configuration)):
  * Specify a storage class unless using a default storage class in your Kubernetes cluster

## Create a deployment

```bash
helm repo add solacecharts https://solacedev.github.io/solace-kubernetes-quickstart/helm-charts
helm install --name my-release solacecharts/pubsubplus
```

## Delete a deployment

```bash
helm delete --purge my-release
kubectl get pvc | grep data-my-release
# Delete any PVCs related to my-release
```
Note: ensure to delete existing PVCs if reusing the same deployment name for a clean new deployment.

## Configuration

The following table lists the configurable parameters of the PubSub+ chart and their default values. For a detailed discussion refer to the [Deployment Guide](/docs/PubSubPlusK8SDeployment.md##pubsub-helm-chart-deployment-considerations).

Override default values using the `--set key=value[,key=value]` argument to `helm install`. For example,
```bash
helm install --name my-release \
  --set solace.redundancy=true,solace.usernameAdminPassword=secretpassword \
  solacecharts/pubsubplus
```

Another option is to create a YAML file containing the values to override and pass that to Helm:

```bash
echo "# Overrides:
solace:
  redundancy: true
  usernameAdminPassword: secretpassword" > my-values.yaml
# Now use the file:
helm install --name my-release -f my-values.yaml solacecharts/pubsubplus
```

For more ways to override default chart values, refer to [Customizing the Helm Chart Before Installing](//helm.sh/docs/using_helm/#customizing-the-chart-before-installing).

| Parameter                      | Description                                                                                             | Default                                                 |
| ------------------------------ | ------------------------------------------------------------------------------------------------------- | ------------------------------------------------------- |
| `nameOverride`                 | Kubernetes objects will be named as `<release-name>-nameOverride`                                       | undefined, default naming is `<release-name>-<chart-name>` |
| `fullnameOverride`             | Kubernetes objects will be named as `fullnameOverride`                                                  | undefined, default naming is `<release-name>-<chart-name>` |
| `solace.redundancy`            | `false` will create a single-node non-HA deployment; `true` will create an HA deployment with Primary, Backup and Monitor nodes | `false` |
| `solace.size`                  | Event broker connection scaling. Options: `dev` (requires minimum resources but no guaranteed performance), `prod100`, `prod1k`, `prod10k`, `prod100k`, `prod200k` | `prod100` | `prod100` |
| `solace.usernameAdminPassword` | The password for the "admin" management user. Will autogenerate it if not provided. **Important:** refer to the #documentation# how to retrieve it and use it for `helm upgrade`. | Autogenerate |
| `solace.timezone`              | Timezone setting for the PubSub+ container. Valid values are tz database time zone names.               | undefined, default is UTC |
| `image.repository`             | The docker repo name and path to the Solace Docker image                                                | `solace/solace-pubsub-standard` from public DockerHub   |
| `image.tag`                    | The Solace Docker image tag. It is recommended to specify an explicit tag for production use            | `latest`                                                |
| `image.pullPolicy`             | Image pull policy                                                                                       | `IfNotPresent`                                          |
| `image.pullSecretName`         | Name of the ImagePullSecret to be used with the Docker registry                                         | undefined, meaning no ImagePullSecret used                |
| `securityContext.enabled`      | `true` enables to using defined `fsGroup` and `runAsUser`. Set to `false` if `fsGroup` and `runAsUser` conflict with PodSecurityPolicy or Openshift SCC settings. | `true` meaning `fsGroup` and `runAsUser` used |
| `securityContext.fsGroup`      | Specifies `fsGroup` in pod security context                                                             | set to default non-zero id 1000002 |
| `securityContext.runAsUser`    | Specifies `runAsUser` in pod security context                                                           | set to default PubSub+ appuser id 1000001 |
| `service.type`                 | How to expose the service: options include ClusterIP, NodePort, LoadBalancer                            | `LoadBalancer`                                          |
| `service.annotations`                 | service.annotations allows to add provider-specific service annotations                          | undefined  |
| `service.ports`                | Define PubSub+ service ports exposed. servicePorts are external, mapping to cluster-local pod containerPorts | initial set of frequently used ports, refer to values.yaml |
| `storage.persistent`           | `false` to use ephemeral storage at pod level; `true` to request persistent storage through a StorageClass | `true`, false is not recommended for production use  |
| `storage.slow`                 | `true` to indicate slow storage used, e.g. for NFS.                                                    | `false` |
| `storage.customVolumeMount`    | customVolumeMount can be used to specify a YAML fragment how the data volume should be mounted  instead of using a storage class. | undefined |
| `storage.useStorageClass`      | Name of the StorageClass to be used to request persistent storage volumes                               | undefined, meaning to use the "default" StorageClass for the Kubernetes cluster |
| `storage.size`                 | Size of the persistent storage to be used; Refer to the Solace documentation for storage configuration requirements | `30Gi` |


