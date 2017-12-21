# Install a Solace Message Router onto a Kubernetes cluster

## Purpose of this repository

This repository explains, in general terms, how to install a Solace VMR in various configurations onto a Kubernetes cluster. To view examples of specific environments see:

- [Installing Solace VMR on Google Kubernetes Engine](https://github.com/SolaceProducts/solace-gke-quickstart)

## Description of Solace VMR

Solace Virtual Message Router (VMR) software provides enterprise-grade messaging capabilities so you can easily enable event-driven communications between applications, IoT devices, microservices and mobile devices across hybrid cloud and multi cloud environments. The Solace VMR supports open APIs and standard protocols including AMQP 1.0, JMS, MQTT, REST and WebSocket, along with all message exchange patterns including publish/subscribe, request/reply, fan-in/fan-out, queueing, streaming and more. The Solace VMR can be deployed in all popular public cloud, private cloud and on-prem environments, and offers both feature parity and interoperability with Solace’s proven hardware appliances and Messaging as a Service offering called Solace Cloud.

VMRs can either be deployed as a 3 node HA cluster or a single node. For simple test environments that need to validate application functionality, a single instance will suffice.
Note that in production or any environment where message loss can not be tolerated, an HA cluster is required.

## How to Deploy a VMR onto Kubernetes

This is a 5 step process:

**Step 1**: Perform any pre-requisites to run Kubernetes in your target environment.  This can be things like create GCP project, install Minikube, etc.

    * The minimum requirements for the Solace VMR small-size deployment are 2 CPUs and 8 GB memory available to the Kubernetes node.

**Step 2**: Use the buttons below to go to the Solace Developer portal and request a Solace Community edition VMR or Evaluation edition VMR. Note that the Community edition supports single-node deployment only.

     This process will return an email with a Download link. Download the Solace VMR image.

     | COMMUNITY EDITION FOR SINGLE NODE | EVALUATION EDITION FOR HA CLUSTER |
     | --- | --- |
     <a href="http://dev.solace.com/downloads/download_vmr-ce-docker" target="_blank">
         <img src="/images/register.png"/>
     </a> 
     <a href="http://dev.solace.com/downloads/download-vmr-evaluation-edition-docker/" target="_blank">
         <img src="/images/register.png"/>
     </a>

**Step 3**: Load the Solace VMR image into a Docker container registry.

**Step 4**: Create a Kubernetes Cluster

**Step 5**: Deploy a Solace Deployment, (Service and Pod), onto the cluster.

The [Kubernetes Helm tool](https://github.com/kubernetes/helm/blob/master/README.mdhttps://github.com/kubernetes/helm/blob/master/README.md ) will be used to manage the deployment. A deployment is defined by a Helm chart, which consists of templates and values. The values specify the particular configuration properties in the templates. 

The following diagram illustrates the template structure used for the Solace Deployment. Note that the bare minimum is shown in this diagram just to give you feel to the relationships and major functions.

![alt text](/images/template_relationship.png "Template Relationship")

First download the following cluster create and deployment script on command line:

```sh
  wget https://raw.githubusercontent.com/SolaceProducts/solace-kubernetes-quickstart/SOL-1244/scripts/start_vmr.sh
  chmod 755 start_vmr.sh
```

For the following variables, substitute `<YourAdminPassword>` with the desired password for the management `admin` user. Substitute `<DockerRepo>`, `<ImageName>` and `<releaseTag>` according to your image in the container registry.

```sh
  PASSWORD=<YourAdminPassword>
  SOLACE_IMAGE_URL=<DockerRepo>.<ImageName>:<releaseTag>
```

Next execute the `start_vmr.sh` script with the required arguments. It will install Helm, initialize it on the current Kubernetes Cluster, download the Solace Deployment chart, then use Helm to build and install the chart on the cluster.

Note: the script will place the Solace Deployment chart in the `solace-kubernetes-quickstart/solace` directory, the `helm` executable will be installed in the `helm` directory - all relative to the directory where the script has been executed.

* This will create and start a small-size non-HA VMR deployment with simple local non-persistent storage:

```sh
  ./start_vmr.sh -p ${PASSWORD} -i ${SOLACE_IMAGE_URL}
```

* This will create and start a small-size HA VMR deployment with dynamically provisioned volumes:

```sh
  ./start_vmr.sh -p ${PASSWORD} -i ${SOLACE_IMAGE_URL} -v values-examples/small-persist-ha-provisionPvc.yaml
```

Note: the `start_vmr.sh` script can only be used to create an initial deployment. To modify a deployment refer to the section [Upgrading/modifying the VMR cluster](#upgrading-the-vmr-cluster).

#### Other VMR deployment configurations

When building the chart, the `values.yaml` located in the created `solace-kubernetes-quickstart/solace` directory is used by Helm for values. The `start_vmr.sh` script replaces this file with a <value-file> specified in the argument `-v <value-file>`. 

The `solace-kubernetes-quickstart/solace/values-examples` directory provides examples for `values.yaml` for several deployment configurations:

* `small-direct-noha` (default if no argument provided): small-size, non-HA, simple local non-persistent storage
* `small-direct-noha-existingVolume`: small-size, non-HA, bind the PVC to an existing external volume in the network
* `small-direct-noha-localDirectory`: small-size, non-HA, bind the PVC to a local directory on the host node
* `small-direct-noha-provisionPvc`: small-size, non-HA, bind the PVC to a provisioned PersistentVolume (PV) in Kubernetes
* `small-persist-ha-provisionPvc`: small-size, HA, to bind the PVC to a provisioned PersistentVolume (PV) in Kubernetes

Similar value-files can be defined extending above examples:

- To open up more service ports for external access, add now ports to the `externalPort` list. For a list of available services and default ports refer to [VMR Configuration Defaults](https://docs.solace.com/Solace-VMR-Set-Up/VMR-Configuration-Defaults.htm) in the Solace customer documentation.

- It is also possible to configure the VMR deployment with more CPU and memory resources e.g.: to support more connections per VMR, by changing the solace `size` in `values.yaml`. The Kubernetes host node resources must be also provisioned accordingly.

* `small` (default): 1.2 CPU, 6 GB memory
* `medium`: 3.5 CPU, 15 GB memory
* `large`: 7.5 CPU, 30 GB memory

### Validate the Deployment

Now you can validate your deployment on command line, in this case an HA cluster is deployed with po/XXX-XXX-solace-0 being the active VMR/pod:

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

Note here several IPs and port.  In this example 104.154.136.44 is the external IP to use.

Note: when using Minikube, there is no integrated LoadBalancer. For a workaround, you can use `minikube service XXX-XXX-solace` to expose the service.

## Gaining admin access to the VMR

<<admin access>>

If you are using a single VMR and used to working with Solace message router console access, this is still available with standard ssh session from any internet at port 22 by default:

```sh

$ssh -p 22 admin@104.154.136.44
Solace - Virtual Message Router (VMR)
Password:

System Software. SolOS-TR Version 8.6.0.1010

Virtual Message Router (Message Routing Node)

Copyright 2004-2017 Solace Corporation. All rights reserved.

This is the Community Edition of the Solace VMR.

XXX-XXX-solace-kubernetes-0>

```

If you are using an HA cluster, it is better to access through the Kubernets pod and not directly via TCP:
Loopback to ssh directly on the pod

```sh

kubectl exec -it XXX-XXX-solace-0  -- bash -c "ssh admin@localhost"

```

Loopback to ssh on your host with a port-forward map

```sh

kubectl port-forward XXX-XXX-solace-0 2222:22 &
ssh -p 2222 admin@localhost

```

For persons who are unfamiliar with the Solace mesage router or would prefer an administration application, the SolAdmin management application is available.  For more information on SolAdmin see the [SolAdmin page](http://dev.solace.com/tech/soladmin/).  To get SolAdmin, visit the Solace [download page](http://dev.solace.com/downloads/) and select OS version desired.  Management IP will be the Public IP associated with youe GCE instance and port will be 8080 by default.

This can also be mapped to individual VMRs in cluster via port-forward:

```sh

kubectl port-forward XXX-XXX-solace-0 8081:8080 &
kubectl port-forward XXX-XXX-solace-1 8081:8080 &
kubectl port-forward XXX-XXX-solace-2 8081:8080 &

```

<<ssh access>>


## Viewing logs
Logs from the currently running container:

```sh

kubectl logs XXX-XXX-solace-0 -c solace

```

Logs from the previously terminated container:

```sh

kubectl logs XXX-XXX-solace-0 -c solace -p

```

## Testing data access to the VMR

To test data traffic though the newly created VMR instance, visit the Solace developer portal and and select your preferred programming language to [send and receive messages](http://dev.solace.com/get-started/send-receive-messages/). Under each language there is a Publish/Subscribe tutorial that will help you get started.

## Upgrading/modifying the VMR cluster

To upgrade/modify the VMR cluster make the required modifications to the chart in the `solace-kubernetes-quickstart/solace` directory as described next then run the `helm` tool from here. When passing multiple `-f <values-file>` to helm, the override priority will be given to the last (right-most) file specified.

To **upgrade** the version of SolOS VMR software running within a Kubernetes cluster:

- Add new version of SolOS to your cantainer registry.
- Create a simple upgrade.yaml file in solace-kubernetes-quickstart/solace directory:

```sh
image:
  repository: <repo>/<project>/solos-vmr
  tag: 8.7.0.XXXXX-evaluation
  pullPolicy: IfNotPresent
```
- Upgrade the Kubernetes release, this will not effect running instances

```sh
../../helm/helm upgrade XXX-XXX . -f values.yaml -f upgrade.yaml
```

- Delete the pod(s) to force them recreated with the new release. 
Important: in an HA deployment delete the pods in order 2,1,0.  Validate Solace redundancy is up and reconsiled before deleting each pod - this can be checked e.g. using the CLI `show redundancy` and `show config-sync` commands or grepping the container logs for `config-sync-check`.

```sh
kubectl delete po/XXX-XXX-solace-<pod-ordinal>
```

Similarly, to **modify** other deployment parameters, e.g. to change the ports exposed via the loadbalancer, you need to upgrade the release with a new set of ports.  In this example we will add the MQTT 1883 tcp port to the loadbalancer.

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

../../helm/helm upgrade  XXXX-XXXX . –f values.yaml –f port_update.yaml
```

Next, delete the pod(s) to force them recreated with the new release as described above in the upgrade case. 

## Deleting a deployment

Use helm to delete a release:

```
# in this case relative to the solace-kubernetes-quickstart/solace directory
../../helm/helm delete XXXX-XXXX
```

Note: in some releases helm may return an error even delete was successful.

Check what has remained from the deployment, which should only return a single line with svc/kubernetes.

```
kubectl get statefulsets,services,pods,pvc,pv
```

Note: in some releases helm may not be able to clean up all the deployment artifacts, e.g.: pvc/ and pv/. If necessary, use `helm delete` to delete those.

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
