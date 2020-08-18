# Solace PubSub+ Software Event Broker - Helm Chart

The [Solace PubSub+ Platform](https://solace.com/products/platform/)'s [software event broker](https://solace.com/products/event-broker/software/) efficiently streams event-driven information between applications, IoT devices and user interfaces running in cloud, on-premises, and hybrid environments using open APIs and protocols like AMQP, JMS, MQTT, REST and WebSocket. It can be installed into a variety of public and private clouds, PaaS, and on-premises environments, and brokers in multiple locations can be linked together in an [event mesh](https://solace.com/what-is-an-event-mesh/) to dynamically share events across the distributed enterprise.

## Overview

This chart bootstraps a single-node or HA deployment of a [Solace PubSub+ Software Event Broker](//solace.com/products/event-broker/software/) on a [Kubernetes](//kubernetes.io) cluster using the [Helm](//helm.sh) package manager.

Detailed documentation is provided in the [Solace PubSub+ Software Event Broker on Kubernetes Documentation](//github.com/SolaceProducts/pubsubplus-kubernetes-quickstart/blob/master/docs/PubSubPlusK8SDeployment.md).

## Prerequisites

* Kubernetes 1.10 or later platform with adequate [CPU and memory](//github.com/SolaceProducts/pubsubplus-kubernetes-quickstart/blob/master/docs/PubSubPlusK8SDeployment.md#cpu-and-memory-requirements) and [storage resources](//github.com/SolaceProducts/pubsubplus-kubernetes-quickstart/blob/master/docs/PubSubPlusK8SDeployment.md#disk-storage) for the targeted scaling tier requirements
* Helm package manager v2 or v3 client installed and configured with Tiller deployed if using Helm v2. Helm v3 is recommended, examples in this document use v3.
* If using a private Docker registry, load the PubSub+ Software Event Broker Docker image and for signed images create an image pull secret
* With persistent storage enabled (see in [Configuration](#config-storageclass)):
  * Specify a storage class unless using a default storage class in your Kubernetes cluster

Also review additional [deployment considerations](//github.com/SolaceProducts/pubsubplus-kubernetes-quickstart/blob/master/docs/PubSubPlusK8SDeployment.md#pubsub-software-event-broker-deployment-considerations).

## Create a deployment

```bash
helm repo add solacecharts https://solaceproducts.github.io/pubsubplus-kubernetes-quickstart/helm-charts
helm install my-release solacecharts/pubsubplus
```

## Use a deployment

Obtain information about the deployment and services:

```bash
helm status my-release
```

Refer to the detailed PubSub+ Kubernetes documentation for:
* [Validating the deployment](//github.com/SolaceProducts/pubsubplus-kubernetes-quickstart/blob/master/docs/PubSubPlusK8SDeployment.md#validating-the-deployment); or
* [Troubleshooting](//github.com/SolaceProducts/pubsubplus-kubernetes-quickstart/blob/master/docs/PubSubPlusK8SDeployment.md#troubleshooting)
* [Modifying or Upgrading](//github.com/SolaceProducts/pubsubplus-kubernetes-quickstart/blob/master/docs/PubSubPlusK8SDeployment.md#modifying-or-upgrading-a-deployment)

## Delete a deployment

```bash
helm delete my-release
kubectl get pvc | grep data-my-release
# Delete any PVCs related to my-release
```
**Important:** Ensure to delete existing PVCs if reusing the same deployment name for a clean new deployment.

## Configuration

The following table lists the configurable parameters of the PubSub+ chart and their default values. For a detailed discussion refer to the [Deployment Considerations](//github.com/SolaceProducts/pubsubplus-kubernetes-quickstart/blob/master/docs/PubSubPlusK8SDeployment.md##pubsub-helm-chart-deployment-considerations) in the PubSub+ Kubernetes documentation.

There are several ways to customize the deployment:

- Override default values using the `--set key=value[,key=value]` argument to `helm install`. For example,
```bash
helm install my-release \
  --set solace.redundancy=true,solace.usernameAdminPassword=secretpassword \
  solacecharts/pubsubplus
```

- Another option is to create a YAML file containing the values to override and pass that to Helm:
```bash
# Create file
echo "# Overrides:
solace:
  redundancy: true
  usernameAdminPassword: secretpassword" > my-values.yaml
# Now use the file:
helm install --name my-release -f my-values.yaml solacecharts/pubsubplus
```
> Note: as an alternative to creating a new file you can [download](https://raw.githubusercontent.com/SolaceProducts/pubsubplus-kubernetes-quickstart/master/pubsubplus/values.yaml) the `values.yaml` file with default values and edit that for overrides.

For more ways to override default chart values, refer to [Customizing the Helm Chart Before Installing](//helm.sh/docs/intro/using_helm/#customizing-the-chart-before-installing).

| Parameter                      | Description                                                                                             | Default                                                 |
| ------------------------------ | ------------------------------------------------------------------------------------------------------- | ------------------------------------------------------- |
| `nameOverride`                 | Kubernetes objects will be named as `<release-name>-nameOverride`                                       | Undefined, default naming is `<release-name>-<chart-name>` |
| `fullnameOverride`             | Kubernetes objects will be named as `fullnameOverride`                                                  | Undefined, default naming is `<release-name>-<chart-name>` |
| `solace.redundancy`            | `false` will create a single-node non-HA deployment; `true` will create an HA deployment with Primary, Backup and Monitor nodes | `false` |
| `solace.size`                  | Event broker connection scaling. Options: `dev` (requires minimum resources but no guaranteed performance), `prod100`, `prod1k`, `prod10k`, `prod100k`, `prod200k` | `prod100` |
| `solace.usernameAdminPassword` | The password for the "admin" management user. Will autogenerate it if not provided. **Important:** refer to the the information from `helm status` how to retrieve it and use it for `helm upgrade`. | Undefined, meaning autogenerate |
| `solace.timezone`              | Timezone setting for the PubSub+ container. Valid values are tz database time zone names.               | Undefined, default is UTC |
| `image.repository`             | The docker repo name and path to the Solace Docker image                                                | `solace/solace-pubsub-standard` from public DockerHub   |
| `image.tag`                    | The Solace Docker image tag. It is recommended to specify an explicit tag for production use For possible tags, refer to the [Solace Docker Hub repo](https://hub.docker.com/r/solace/solace-pubsub-standard/tags) | `latest`                                                |
| `image.pullPolicy`             | Image pull policy                                                                                       | `IfNotPresent`                                          |
| `image.pullSecretName`         | Name of the ImagePullSecret to be used with the Docker registry                                         | Undefined, meaning no ImagePullSecret used                |
| `securityContext.enabled`      | `true` enables to using defined `fsGroup` and `runAsUser`. Set to `false` if `fsGroup` and `runAsUser` conflict with PodSecurityPolicy or Openshift SCC settings. | `true` meaning `fsGroup` and `runAsUser` used |
| `securityContext.fsGroup`      | Specifies `fsGroup` in pod security context                                                             | set to default non-zero id 1000002 |
| `securityContext.runAsUser`    | Specifies `runAsUser` in pod security context                                                           | set to default PubSub+ appuser id 1000001 |
| `serviceAccount.create`        | `true` will create a service account dedicated to the deployment in the namespace                       | `true` |
| `serviceAccount.name`          | Refer to https://helm.sh/docs/topics/chart_best_practices/rbac/#using-rbac-resources                    | Undefined |
| `service.type`                 | How to expose the service: options include ClusterIP, NodePort, LoadBalancer                            | `LoadBalancer`                                          |
| `service.annotations`                 | service.annotations allows to add provider-specific service annotations                          | Undefined  |
| `service.ports`                | Define PubSub+ service ports exposed. servicePorts are external, mapping to cluster-local pod containerPorts | initial set of frequently used ports, refer to values.yaml |
| `storage.persistent`           | `false` to use ephemeral storage at pod level; `true` to request persistent storage through a StorageClass | `true`, false is not recommended for production use  |
| `storage.slow`                 | `true` to indicate slow storage used, e.g. for NFS.                                                    | `false` |
| `storage.customVolumeMount`    | customVolumeMount can be used to specify a YAML fragment how the data volume should be mounted  instead of using a storage class. | Undefined |
| `storage.useStorageClass` <a name="config-storageclass"></a> | Name of the StorageClass to be used to request persistent storage volumes                               | Undefined, meaning to use the "default" StorageClass for the Kubernetes cluster |
| `storage.size`                 | Size of the persistent storage to be used; Refer to the Solace documentation for storage configuration requirements | `30Gi` |



