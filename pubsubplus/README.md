# Solace PubSub+ Message Broker Helm Chart

This chart bootstraps a single-node or HA deployment of a [Solace PubSub+](https://solace.com/products/) message broker on a [Kubernetes](http://kubernetes.io) cluster using the [Helm](https://helm.sh) package manager.

## Solace Helm Chart Configuration

//helm.sh/docs/using_helm/#customizing-the-chart-before-installing

The following table lists the configurable parameters of the Solace chart and their default values.

Specify each parameter using the `--set key=value[,key=value]` argument to `helm install`. For example,

```bash
$ helm install --name my-release \
  --set solace.redundancy=true,solace.usernameAdminPassword=secretpassword <solace-chart-location>
```

| Parameter                      | Description                                                                                             | Default                                                 |
| ------------------------------ | ------------------------------------------------------------------------------------------------------- | ------------------------------------------------------- |
| `solace.redundancy`            | `false` will create a single-node non-HA deployment; `true` will create an HA deployment with Primary, Backup and Monitor nodes | `false`                         |
| `solace.size`                  | Connection scaling. Options: `dev` (requires minimum resources but no guaranteed performance), `prod100`, `prod1k`, `prod10k`, `prod100k`, `prod200k` | `prod100` |
| `solace.usernameAdminPassword` | The password for the "admin" management user. Must be provided for HA deployment (`solace.redundancy=true`). Will autogenerate it if not provided for non-HA deployment. | Auto-generate |
| `image.repository`             | The docker repo name and path to the Solace Docker image                                                | `solace/solace-pubsub-standard` from public DockerHub   |
| `image.tag`                    | The Solace Docker image tag. It is recommended to specify an explicit tag for production use            | `latest`                                                |
| `image.pullPolicy`             | Image pull policy                                                                                       | `IfNotPresent`                                          |
| `image.pullSecretName`         | Name of the ImagePullSecret to be used with the Docker registry                                         | not set, meaning no ImagePullSecret used                |
| `service.type`                 | How to expose the service: options include ClusterIP, NodePort, LoadBalancer                            | `LoadBalancer`                                          |
| `service.addExternalPort`      | Use to define additional Solace service ports exposed externally, with mapping to pod targetport        | not set                                                 |
| `service.addInternalPort`      | For any matching targetport in 'service.addExternalPort', this property will expose that port at the pod-level first | not set                                    |
| `storage.persistent`           | `false` to use ephemeral storage at pod level; `true` to request persistent storage through a StorageClass | `true`, false is not recommended for production use  |
| `storage.useStorageClass`      | Name of the StorageClass to be used to request persistent storage volumes                               | `standard`                                              |
| `storage.size`                 | Size of the persistent storage to be used; Refer to the Solace documentation for storage configuration requirements | `20Gi`                                      |


For more ways to override default values, refer to [Customizing the Chart Before Installing](//helm.sh/docs/using_helm/#customizing-the-chart-before-installing).