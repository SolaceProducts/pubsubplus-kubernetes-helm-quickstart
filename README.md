[![Build Status](https://travis-ci.org/SolaceProducts/solace-kubernetes-quickstart.svg?branch=master)](https://travis-ci.org/SolaceProducts/solace-kubernetes-quickstart)

# Install a Solace PubSub+ Software Message Broker onto a Kubernetes cluster

## Purpose of this repository

This repository explains how to install a Solace PubSub+ Software Message Broker in various configurations onto a Kubernetes cluster using the Helm tool. This guide is intended mainly for development and demo purposes.

This document is applicable to any platform supporting Kubernetes, with specific hints on how to set up a simple single-node MiniKube deployment on a Unix-based machine. To view examples of other platforms see:

- [Deploying a Solace PubSub+ Software Message Broker HA group onto a Google Kubernetes Engine](https://github.com/SolaceProducts/solace-gke-quickstart )
- [Deploying a Solace PubSub+ Software Message Broker HA Group onto an OpenShift 3.7 or 3.9 platform](https://github.com/SolaceProducts/solace-openshift-quickstart )
- Deploying a Solace PubSub+ Software Message Broker HA Group onto Amazon EKS (Amazon Elastic Container Service for Kubernetes): follow the [AWS documentation](https://docs.aws.amazon.com/eks/latest/userguide/getting-started.html ) to set up EKS then this guide to deploy.

## Description of the Solace PubSub+ Software Message Broker

The Solace PubSub+ software message broker meets the needs of big data, cloud migration, and Internet-of-Things initiatives, and enables microservices and event-driven architecture. Capabilities include topic-based publish/subscribe, request/reply, message queues/queueing, and data streaming for IoT devices and mobile/web apps. The message broker supports open APIs and standard protocols including AMQP, JMS, MQTT, REST, and WebSocket. Moreover, it can be deployed in on-premise datacenters, natively within private and public clouds, and across complex hybrid cloud environments.

Solace PubSub+ software message brokers can be deployed in either a 3-node High-Availability (HA) cluster, or as a single node deployment. For simple test environments that need only to validate application functionality, a single instance will suffice. Note that in production, or any environment where message loss cannot be tolerated, an HA cluster is required.

## How to deploy a message broker onto Kubernetes

In this quick start we go through the steps to set up a small-size message broker either as a single stand-alone instance, or in a 3-node HA cluster. If you are interested in other message broker configurations or sizes, refer to the [Deployment Configurations](#other-message-broker-deployment-configurations) section.

This is a 4 step process:

### Step 1: 

Perform any prerequisites to run Kubernetes in your target environment. These tasks may include creating a GCP project, installing [MiniKube](https://github.com/kubernetes/minikube/blob/master/README.md ), etc. You will also need following tools:

* Install [`kubectl`](https://kubernetes.io/docs/tasks/tools/install-kubectl/ ).
* Installation of [`docker`](https://docs.docker.com/get-started/ ) may also be required depending on your environment.

### Step 2: 

Create a Kubernetes platform. This may be a single node or a multi-node cluster.

* The recommended requirements for the smallest message broker deployment (`dev100`) is 2 CPUs and 2 GBs of memory available for each message broker node. For requirements supporting larger deployments, refer to the [Other Message Broker Deployment Configurations](#other-message-broker-deployment-configurations) section.

> Note: If using MiniKube, `minikube start` will also setup Kubernetes. By default it will start with 2 CPU and 2 GB memory allocated. For more granular control, use the `--cpus` and `--memory` options.

Before continuing, ensure the `kubectl get svc` command returns the `kubernetes` service listed.

### Step 3 (Optional): 

Obtain the Solace PubSub+ message broker docker image and load it into a [docker container registry](https://docs.docker.com/registry/ ).

**Hint:** You may skip the rest of this step if using the free PubSub+ Standard Edition available from the [Solace public Docker Hub registry](https://hub.docker.com/r/solace/solace-pubsub-standard/tags/ ). The docker registry reference to use will be `solace/solace-pubsub-standard:<TagName>`. 

> Note: If using MiniKube you can [reuse its docker daemon](https://github.com/kubernetes/minikube/blob/master/docs/reusing_the_docker_daemon.md ) and load the image into the local registry.

To get the message broker docker image, go to the Solace Developer Portal and download the Solace PubSub+ software message broker as a **docker** image or obtain your version from Solace Support.

| PubSub+ Standard<br/>Docker Image | PubSub+ Enterprise Evaluation Edition<br/>Docker Image
| :---: | :---: |
| Free, up to 1k simultaneous connections,<br/>up to 10k messages per second | 90-day trial version, unlimited |
| [Download Standard docker image](http://dev.solace.com/downloads/) | [Download Evaluation docker image](http://dev.solace.com/downloads#eval) |

To load the docker image into a docker registry, follow the steps specific to the registry you are using.

### Step 4: 

Deploy message broker Pods and Service to the cluster.

The [Kubernetes `helm`](https://github.com/kubernetes/helm/blob/master/README.md ) tool is used to manage this deployment. A deployment is defined by a "helm chart", which consists of templates and values. The values specify the particular configuration properties in the templates.

The following diagram illustrates the template structure used for the Solace Deployment chart. Note that the minimum is shown in this diagram to give you some background regarding the relationships and major functions.

![alt text](/images/template_relationship.png "Template Relationship")

* First, clone this repo, which includes helper scripts and the `solace` helm chart:

```sh
mkdir ~/workspace; cd ~/workspace
git clone https://github.com/SolaceDev/solace-kubernetes-quickstart.git
cd solace-kubernetes-quickstart/solace    # location of the solace helm chart
```

* Next, prepare your environment and customize your chart by executing the `configure.sh` script and pass it the required parameters: 

| Parameter     | Description                                                                    |
|---------------|--------------------------------------------------------------------------------|
| `-p`          | REQUIRED: The password for the management `admin` user |
| `-i`          | OPTIONAL: The Solace image reference in the docker container registry in the form `<DockerRepo>.<ImageName>:<releaseTag>` from [Step 3](#step-3-optional). The default is to use `solace/solace-pubsub-standard:latest`. NOTE: If providing a reference, the `<DockerRepo>.` is not required if using a local repo (e.g. when using MiniKube) |
| `-c`          | OPTIONAL: The cloud environment you will be running in, current options are [aws\|gcp]. NOTE: if you are not using dynamic provisioned persistent disks, or, if you are running a local MiniKube environment, this option can be left out. |
| `-v`          | OPTIONAL: The path to a `values.yaml` example/custom file to use. The default file is `values-examples/dev100-direct-noha.yaml` |

The location of the `configure.sh` script is in the `../scripts` directory, relative to the `solace` chart. Executing the configuration script will install the required version of the `helm` tool if needed, as well as customize the `solace` helm chart to your desired configuration.

When customizing the `solace` chart by the script, the `values.yaml` located in the root of the chart will be replaced with what is specified in the argument `-v <value-file>`. A number of examples are provided in the `values-examples/` directory, for details refer to [this section](#other-message-broker-deployment-configurations). 

Running the script, with no optional parameters specified, a `development` non-HA message broker deployment will be prepared with up to 100 connections using simple local non-persistent storage, using the latest Solace PubSub+ Standard edition message broker image from the Solace public Docker Hub registry:

```sh
cd ~/workspace/solace-kubernetes-quickstart/solace
../scripts/configure.sh -p <ADMIN_PASSWORD>   # add the -c <CLOUD_PROVIDER> option if using aws or gke
```

The following example shows how to use all parameters and will prepare a `production` HA message broker deployment, supporting up to 1000 connections, using a provisioned PersistentVolume (PV) storage, using the image pulled from the SOLACE_IMAGE_URL registry reference:

```sh
cd ~/workspace/solace-kubernetes-quickstart/solace
../scripts/configure.sh -p <ADMIN_PASSWORD> -i <SOLACE_IMAGE_URL> -c <CLOUD_PROVIDER> -v values-examples/prod1k-persist-ha-provisionPvc.yaml
```

* Finally, use `helm` to install the deployment from the `solace` chart location, using your generated `values.yaml` file:

```sh
cd ~/workspace/solace-kubernetes-quickstart/solace
helm install . -f values.yaml
# Wait until all pods running and ready and the active message broker pod label is "active=true"
watch kubectl get pods --show-labels
```

To modify a deployment, refer to the section [Upgrading/modifying the message broker cluster](#upgradingmodifying-the-message-broker-cluster). If you need to start over then refer to the section [Deleting a deployment](#deleting-a-deployment).

### Validate the Deployment

Now you can validate your deployment on the command line. In this example an HA cluster is deployed with po/XXX-XXX-solace-0 being the active message broker/pod. The notation XXX-XXX is used for the unique release name that `helm` dynamically generates, e.g: "tinseled-lamb".

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

## Gaining admin access to the message broker

Refer to the [Management Tools section](https://docs.solace.com/Management-Tools.htm ) of the online documentation to learn more about the available tools. The WebUI is the recommended simplest way to administer the message broker for common tasks.

### WebUI, SolAdmin and SEMP access

Use the Load Balancer's external Public IP at port 8080 to access these services.

### Solace CLI access

If you are using a single message broker and are used to working with a CLI message broker console access, you can SSH into the message broker as the `admin` user using the Load Balancer's external Public IP:

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

If you are using an HA cluster, it is better to access the CLI through the Kubernets pod and not directly via SSH.

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

This can also be mapped to individual message brokers in the cluster via port-forward:

```
kubectl port-forward XXX-XXX-solace-0 8081:8080 &
kubectl port-forward XXX-XXX-solace-1 8082:8080 &
kubectl port-forward XXX-XXX-solace-2 8083:8080 &
```

For SSH access to individual message brokers use:

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

To test data traffic though the newly created message broker instance, visit the Solace Developer Portal and and select your preferred programming language in [send and receive messages](http://dev.solace.com/get-started/send-receive-messages/). Under each language there is a Publish/Subscribe tutorial that will help you get started and provide the specific default port to use.

Use the external Public IP to access the cluster. If a port required for a protocol is not opened, refer to the next section on how to open it up by modifying the cluster.

## Upgrading/modifying the message broker cluster

To upgrade/modify the message broker cluster, make the required modifications to the chart in the `solace-kubernetes-quickstart/solace` directory as described next, then run the `helm` tool from here. When passing multiple `-f <values-file>` to helm, the override priority will be given to the last (right-most) file specified.

### Upgrading the cluster

To **upgrade** the version of the message broker running within a Kubernetes cluster:

- Add the new version of the message broker to your container registry.
- Create a simple upgrade.yaml file in solace-kubernetes-quickstart/solace directory, e.g.:

```sh
image:
  repository: <repo>/<project>/solace-pubsub-standard
  tag: NEW.VERSION.XXXXX
  pullPolicy: IfNotPresent
```
- Upgrade the Kubernetes release, this will not effect running instances

```sh
cd ~/workspace/solace-kubernetes-quickstart/solace
helm upgrade XXX-XXX . -f values.yaml -f upgrade.yaml
```

- Delete the pod(s) to force them to be recreated with the new release. 

```sh
kubectl delete po/XXX-XXX-solace-<pod-ordinal>
```
> Important: In an HA deployment, delete the pods in this order: 2,1,0 (i.e. Monitoring Node, Backup Messaging Node, Primary Messaging Node). Confirm that the message broker redundancy is up and reconciled before deleting each pod - this can be verified using the CLI `show redundancy` and `show config-sync` commands on the message broker, or by grepping the message broker container logs for `config-sync-check`.

### Modifying the cluster

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

## Deleting a deployment

Use Helm to delete a deployment, also called a release:

```
helm delete XXX-XXX
```

> Note: In some versions, Helm may return an error even if the deletion was successful.

Check what has remained from the deployment, which should only return a single line with svc/kubernetes.

```
kubectl get statefulsets,services,pods,pvc,pv
```
> Note: In some versions, Helm may not be able to clean up all the deployment artifacts, e.g.: pvc/ and pv/. Check their existence with `kubectl get all` and if necessary, use `kubectl delete` to delete those.

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

    * `dev100` (default): up to 100 connections, minimum requirements: 1 CPU, 1 GB memory
    * `prod100`: up to 100 connections, minimum requirements: 2 CPU, 2 GB memory
    * `prod1k`: up to 1,000 connections, minimum requirements: 2 CPU, 4 GB memory
    * `prod10k`: up to 10,000 connections, minimum requirements: 4 CPU, 12 GB memory
    * `prod100k`: up to 100,000 connections, minimum requirements: 8 CPU, 28 GB memory
    * `prod200k`: up to 200,000 connections, minimum requirements: 12 CPU, 56 GB memory

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
