[![Build Status](https://travis-ci.org/SolaceProducts/solace-kubernetes-quickstart.svg?branch=master)](https://travis-ci.org/SolaceProducts/solace-kubernetes-quickstart)

# Install a Solace PubSub+ Software Message Broker onto a Kubernetes cluster

## Purpose of this repository

This repository explains how to install a Solace PubSub+ Software Message Broker in various configurations onto a Kubernetes cluster using the Helm tool. To view examples of specific environments see:

- [Deploying a Solace PubSub+ Software Message Broker HA group onto a Google Kubernetes Engine](https://github.com/SolaceProducts/solace-gke-quickstart)

## Description of the Solace PubSub+ Software Message Broker

The Solace PubSub+ software message broker meets the needs of big data, cloud migration, and Internet-of-Things initiatives, and enables microservices and event-driven architecture. Capabilities include topic-based publish/subscribe, request/reply, message queues/queueing, and data streaming for IoT devices and mobile/web apps. The message broker supports open APIs and standard protocols including AMQP, JMS, MQTT, REST, and WebSocket. As well, it can be deployed in on-premise datacenters, natively within private and public clouds, and across complex hybrid cloud environments.

Solace PubSub+ software message brokers can deployed in either 3 node HA clusters or as single nodes. For simple test environments that need only to validate application functionality, a single instance will suffice. Note that in production, or any environment where message loss cannot be tolerated, an HA cluster is required.

## How to deploy a message broker onto Kubernetes

In this quick start we go through the steps to set up a small-size message broker either as a single, stand-alone instance or in a 3-node, HA cluster. If you are interested in other message broker configurations or sizes, refer to the last section called Other Message Broker Deployment Configurations.

This is a 5 step process:

### Step 1: 

Perform any prerequisites to run Kubernetes in your target environment. These can include tasks like creating a GCP project, installing [MiniKube](https://github.com/kubernetes/minikube/blob/master/README.md ), etc.

* Install [`kubectl`](https://kubernetes.io/docs/tasks/tools/install-kubectl/ ).
* Installation of [`docker`](https://docs.docker.com/get-started/ ) may also be required depending on your environment.

### Step 2: 

Go to the Solace Developer Portal and download the Solace PubSub+ software message broker for Docker image.

You can use this quick start with either PubSub+ `Standard` or PubSub+ `Enterprise Evaluation Edition`.

| PubSub+ Standard | PubSub+ Enterprise Evaluation Edition
| :---: | :---: |
| Free, up to 1k simultaneous connections,<br/>up to 10k messages per second | 90-day trial version, unlimited |
| <a href="http://dev.solace.com/downloads/download_vmr-ce-docker" target="_blank"><img src="images/register.png"/></a> | <a href="http://dev.solace.com/downloads/download-vmr-evaluation-edition-docker/" target="_blank"><img src="images/register.png"/></a> |
 
<br>
<br>
 
### Step 3: 

Load the message broker image into a Docker container registry.

> If using MiniKube you can [reuse the Docker daemon](https://github.com/kubernetes/minikube/blob/master/docs/reusing_the_docker_daemon.md ) and load the image into the local registry.  

### Step 4: 

Create a Kubernetes platform. This may be a single node or a multi-node cluster.

* The minimum recommended resources for the smallest Solace message broker deployment are 2 CPU and 2 GB memory available to the Kubernetes node. For requirements supporting larger deployments refer to the [Deployment Configurations](#other-message-broker-deployment-configurations) section.

> If using MiniKube, `minikube start` will also setup Kubernetes. By default it will start with 2 CPU and 2 GB memory allocated. Use `--cpus` and `--memory` for other options.

Before continuing ensure the `kubectl get svc` command returns the `kubernetes` service listed.

### Step 5: 

Deploy Solace message broker Pods and Service to the cluster.

The [Kubernetes Helm](https://github.com/kubernetes/helm/blob/master/README.md ) tool is used to manage the deployment. A deployment is defined by a Helm chart, which consists of templates and values. The values specify the particular configuration properties in the templates. 

The following diagram illustrates the template structure used for the Solace Deployment chart. Note that the bare minimum is shown in this diagram just to give you some background regarding the relationships and major functions.

![alt text](/images/template_relationship.png "Template Relationship")

First, download the following configuration script on command line:

```sh
wget https://raw.githubusercontent.com/SolaceProducts/solace-kubernetes-quickstart/master/scripts/configure.sh
chmod 755 configure.sh
```

Next, execute the config script with passing parameters. For convenience the following variables can be defined. Substitute `<YourAdminPassword>` with the desired password for the management `admin` user; substitute `<DockerRepo>`, `<ImageName>` and `<releaseTag>` according to your image in the container registry; substitute `<YourCloudProvider>` with the cloud environment you will be running in, current options are [aws|gcp] - if you are not using dynamic provisioned persistent disks, this can be left out.

```sh
PASSWORD=<YourAdminPassword>
SOLACE_IMAGE_URL=<DockerRepo>.<ImageName>:<releaseTag>  # <DockerRepo> is not required if using local repo e.g.: with MiniKube
CLOUD_PROVIDER=<YourCloudProvider>                      # only use for aws|gcp, skip otherwise including when using MiniKube
```

Executing the configuration script will install the required version of the `helm` tool, clone this git repo then prepare the `solace` helm chart.

Note: the script will place the Solace Deployment chart in the `solace-kubernetes-quickstart/solace` directory, and the `helm` executable will be installed in the `helm` directory - all relative to the directory where the script has been executed.

When preparing the `solace` chart by the script, the `values.yaml` located in the cloned `solace-kubernetes-quickstart/solace` directory will be replaced with what is specified in the argument `-v <value-file>`. A number of examples are provided in the `values-examples/` directory, for details refer to [this section](#other-message-broker-deployment-configurations).

* By default a `development` non-HA message broker deployment will be prepared supporting up to 100 connections using simple local non-persistent storage:

```sh
./configure.sh -p ${PASSWORD} -i ${SOLACE_IMAGE_URL}
```

* This will prepare a `production` HA message broker deployment, supporting up to 1000 connections, using a provisioned PersistentVolume (PV) storage:

```sh
./configure.sh -p ${PASSWORD} -i ${SOLACE_IMAGE_URL} -c ${CLOUD_PROVIDER} -v values-examples/prod1k-persist-ha-provisionPvc.yaml
```

Finally, use `helm` to install the deployment from the `solace` chart location, based on the contents of `values.yaml`:

```sh
cd solace-kubernetes-quickstart/solace
../../helm/helm install . -f values.yaml
```

To modify a deployment, refer to the section [Upgrading/modifying the message broker cluster](#upgradingmodifying-the-message-broker-cluster). If you need to start over then refer to the section [Deleting a deployment](#deleting-a-deployment).

### Validate the Deployment

Now you can validate your deployment on command line, in this case an HA cluster is deployed with po/XXX-XXX-solace-0 being the active message broker/pod. The notion XXX-XXX is used for the release name that `helm` dynamically generates, e.g: "tinseled-lamb".

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
po/XXX-XXX-solace-1   0/1       Running   0          3m
po/XXX-XXX-solace-2   0/1       Running   0          3m
NAME                               STATUS    VOLUME                                     CAPACITY   ACCESS MODES   STORAGECLASS              AGE
pvc/data-XXX-XXX-solace-0   Bound     pvc-74d9ceb3-d492-11e7-b95e-42010a800173   30Gi       RWO            XXX-XXX-standard   3m
pvc/data-XXX-XXX-solace-1   Bound     pvc-74dce76f-d492-11e7-b95e-42010a800173   30Gi       RWO            XXX-XXX-standard   3m
pvc/data-XXX-XXX-solace-2   Bound     pvc-74e12b36-d492-11e7-b95e-42010a800173   30Gi       RWO            XXX-XXX-standard   3m
NAME                                          CAPACITY   ACCESS MODES   RECLAIM POLICY   STATUS    CLAIM                                  STORAGECLASS              REASON    AGE
pv/pvc-74d9ceb3-d492-11e7-b95e-42010a800173   30Gi       RWO            Delete           Bound     default/data-XXX-XXX-solace-0   XXX-XXX-standard             3m
pv/pvc-74dce76f-d492-11e7-b95e-42010a800173   30Gi       RWO            Delete           Bound     default/data-XXX-XXX-solace-1   XXX-XXX-standard             3m
pv/pvc-74e12b36-d492-11e7-b95e-42010a800173   30Gi       RWO            Delete           Bound     default/data-XXX-XXX-solace-2   XXX-XXX-standard             3m


prompt:~$ kubectl describe service XXX-XX-solace
Name:                     XXX-XX-solace
Namespace:                default
Labels:                   app=solace
                          chart=solace-0.1.0
                          heritage=Tiller
                          release=XXX-XX
Annotations:              <none>
Selector:                 app=solace,release=XXX-XXX
Type:                     LoadBalancer
IP:                       10.15.249.186
LoadBalancer Ingress:     35.202.131.158
Port:                     ssh  22/TCP
TargetPort:               22/TCP
NodePort:                 ssh  32656/TCP
Endpoints:                10.12.7.6:22
Port:                     semp  8080/TCP
TargetPort:               8080/TCP
NodePort:                 semp  32394/TCP
Endpoints:                10.12.7.6:8080
Port:                     smf  55555/TCP
TargetPort:               55555/TCP
NodePort:                 smf  31766/TCP
Endpoints:                10.12.7.6:55555
Session Affinity:         None
External Traffic Policy:  Cluster
:
:

```

Generally all services including management and messaging are accessible through a load balancer. In above example `35.202.131.158` is the Load Balancer's external Public IP to use.

> when using MiniKube, there is no integrated LoadBalancer. For a workaround, you can use `minikube service XXX-XXX-solace` to expose the services. Services will be accessible directly using mapped ports which can be obtained from `kubectl describe service XXX-XX-solace`.

## Gaining admin access to the message broker

If you are using a single message broker and used to working with CLI Solace PubSub+ message broker console access, this is still available with standard ssh session from any internet at port 22 by default:

```sh

$ssh -p 22 admin@35.202.131.158
Solace PubSub+ Standard
Password:

Solace PubSub+ Standard Version 8.10.0.1057

The Solace PubSub+ Standard is proprietary software of
Solace Corporation. By accessing the Solace PubSub+ Standard
you are agreeing to the license terms and conditions located at
http://www.solace.com/license-software

Copyright 2004-2018 Solace Corporation. All rights reserved.

To purchase product support, please contact Solace at:
http://dev.solace.com/contact-us/

Operating Mode: Message Routing Node

XXX-XXX-solace-0>
```

If you are using an HA cluster, it is better to access CLI through the Kubernets pod and not directly via TCP:

* Loopback to ssh directly on the pod

```sh
kubectl exec -it XXX-XXX-solace-0  -- bash -c "ssh admin@localhost"
```

* Loopback to ssh on your host with a port-forward map

```sh
kubectl port-forward XXX-XXX-solace-0 2222:22 &
ssh -p 2222 admin@localhost
```

For persons who are unfamiliar with the Solace PubSub+ message broker, or would prefer an administration application, the SolAdmin management application is available. For more information on SolAdmin see the [SolAdmin page](http://dev.solace.com/tech/soladmin/).  To get SolAdmin, visit the Solace [download page](http://dev.solace.com/downloads/) and select the OS version desired.  Management IP will be the Public IP associated with youe GCE instance and port will be 8080 by default.

This can also be mapped to individual message brokers in the cluster via port-forward:

```s
kubectl port-forward XXX-XXX-solace-0 8081:8080 &
kubectl port-forward XXX-XXX-solace-1 8081:8080 &
kubectl port-forward XXX-XXX-solace-2 8081:8080 &
```

For ssh access to the individual message brokers use:

```sh
kubectl exec -it XXX-XXX-solace-<pod-ordinal> -- bash
```

## Viewing logs
Logs from the currently running container:

```sh
kubectl logs XXX-XXX-solace-0 -c solace
```

Logs from the previously terminated container:

```sh
kubectl logs XXX-XXX-solace-0 -c solace -p
```

## Testing data access to the message broker

To test data traffic though the newly created message broker instance, visit the Solace Developer Portal and and select your preferred programming language to [send and receive messages](http://dev.solace.com/get-started/send-receive-messages/). Under each language there is a Publish/Subscribe tutorial that will help you get started.

Use the external Public IP to access the cluster. If a port required for a protocol is not opened refer to the next section how to open it up by modifying the cluster.

## Upgrading/modifying the message broker cluster

To upgrade/modify the message broker cluster, make the required modifications to the chart in the `solace-kubernetes-quickstart/solace` directory as described next, then run the `helm` tool from here. When passing multiple `-f <values-file>` to helm, the override priority will be given to the last (right-most) file specified.

To **upgrade** the version of the message broker running within a Kubernetes cluster:

- Add new version of the message broker to your container registry.
- Create a simple upgrade.yaml file in solace-kubernetes-quickstart/solace directory, e.g.:

```sh
image:
  repository: <repo>/<project>/solace-pubsub-standard
  tag: 8.10.0.XXXXX
  pullPolicy: IfNotPresent
```
- Upgrade the Kubernetes release, this will not effect running instances

```sh
# Relative to the solace-kubernetes-quickstart/solace directory
../../helm/helm upgrade XXX-XXX . -f values.yaml -f upgrade.yaml
```

- Delete the pod(s) to force them to be recreated with the new release. 

    Important: In an HA deployment, delete the pods in this order: 2,1,0.  Validate message broker redundancy is up and reconciled before deleting each pod - this can be checked e.g. using the CLI `show redundancy` and `show config-sync` commands or grepping the container logs for `config-sync-check`.

```sh
kubectl delete po/XXX-XXX-solace-<pod-ordinal>
```

Similarly, to **modify** other deployment parameters, e.g. to change the ports exposed via the loadbalancer, you need to upgrade the release with a new set of ports. In this example we will add the MQTT 1883 tcp port to the loadbalancer.

```
tee ./port-update.yaml <<-EOF
service:
  internal: false
  type: LoadBalancer
  externalPort:
    - port: 22
      protocol: TCP
      name: ssh
    - port: 8080
      protocol: TCP
      name: semp
    - port: 55555
      protocol: TCP
      name: smf
   - port: 1883
      protocol: TCP
      name: mqtt    
  internalPort:
    - port: 80
      protocol: TCP
    - port: 8080
      protocol: TCP
    - port: 443
      protocol: TCP
    - port: 8443
      protocol: TCP
    - port: 55555
      protocol: TCP
    - port: 22
      protocol: TCP
   - port: 1883
      protocol: TCP
EOF

# Relative to the solace-kubernetes-quickstart/solace directory
../../helm/helm upgrade  XXXX-XXXX . –f values.yaml –f port_update.yaml
```

Next, delete the pod(s) to force them to be recreated with the new release as described above in the upgrade case. 

## Deleting a deployment

Use Helm to delete a deployment, also called a release:

```
# Relative to the solace-kubernetes-quickstart/solace directory
../../helm/helm delete XXX-XXX
```

Note: In some versions, Helm may return an error even if the deletion was successful.

Check what has remained from the deployment, which should only return a single line with svc/kubernetes.

```
kubectl get statefulsets,services,pods,pvc,pv
```

Note: In some versions, Helm may not be able to clean up all the deployment artifacts, e.g.: pvc/ and pv/. Check their existence with `kubectl get all` and if necessary, use `kubectl delete` to delete those.

## Other Message Broker Deployment Configurations

The `solace-kubernetes-quickstart/solace/values-examples` directory provides examples for `values.yaml` for several deployment configurations:

* `dev100-direct-noha` (default if no argument provided): for development purposes, supports up to 100 connections, non-HA, simple local non-persistent storage
* `prod1k-direct-noha`: production, up to 1000 connections, non-HA, simple local non-persistent storage
* `prod1k-direct-noha-existingVolume`: production, up to 1000 connections, non-HA, bind the PVC to an existing external volume in the network
* `prod1k-direct-noha-localDirectory`: production, up to 1000 connections, non-HA, bind the PVC to a local directory on the host node
* `prod1k-direct-noha-provisionPvc`: production, up to 1000 connections, non-HA, bind the PVC to a provisioned PersistentVolume (PV) in Kubernetes
* `prod1k-persist-ha-provisionPvc`: production, up to 1000 connections, HA, to bind the PVC to a provisioned PersistentVolume (PV) in Kubernetes

Similar value-files can be defined extending above examples:

- To open up more service ports for external access, add new ports to the `externalPort` list. For a list of available services and default ports refer to [Software Message Broker Configuration Defaults](https://docs.solace.com/Configuring-and-Managing/SW-Broker-Specific-Config/SW-Broker-Configuration-Defaults.htm) in the Solace customer documentation.

- It is also possible to configure the message broker deployment with different CPU and memory resources to support more connections per message broker, by changing the solace `size` in `values.yaml`. The Kubernetes host node resources must be also provisioned accordingly.

    * `dev100` (default): up to 100 connections, requires 1 CPU, 1 GB memory
    * `prod100`: up to 100 connections, requires 2 CPU, 2 GB memory
    * `prod1k`: up to 1,000 connections, requires 2 CPU, 4 GB memory
    * `prod10k`: up to 10,000 connections, requires 4 CPU, 12 GB memory
    * `prod100k`: up to 100,000 connections, requires 8 CPU, 28 GB memory
    * `prod200k`: up to 200,000 connections, requires 12 CPU, 56 GB memory

## Contributing

Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details on our code of conduct, and the process for submitting pull requests to us.

## Authors

See the list of [contributors](https://github.com/SolaceProducts/solace-kubernetes-quickstart/graphs/contributors) who participated in this project.

## License

This project is licensed under the Apache License, Version 2.0. - See the [LICENSE](LICENSE) file for details.

## Resources

For more information about Solace technology in general please visit these resources:

- The Solace Developer Portal website at: http://dev.solace.com
- Understanding [Solace technology.](http://dev.solace.com/tech/)
- Ask the [Solace community](http://dev.solace.com/community/).