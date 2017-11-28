# Install a Solace Message Router onto a Kubernetes cluster

## Purpose of this repository

This repository explains, in general terms, how to install a Solace VMR in standalone non-HA configuration onto a Kubernetes cluster.  To view examples of specific enviroments see:

- [Installing Solace VMR on Google Compute Engine](https://github.com/SolaceProducts/solace-gke-quickstart)

## Description of Solace VMR

The Solace Virtual Message Router (VMR) provides enterprise-grade messaging capabilities deployable in any computing environment. The VMR provides the same rich feature set as Solace’s proven hardware appliances, with the same open protocol support, APIs and common management. The VMR can be deployed in the datacenter or natively within all popular private and public clouds.

## How to Deploy a VMR onto Kubernetes

This is a 5 step process:

1. Perform any pre-requisites to run Kubernetes in your target enviroment.  This can be things like create GCP project, install Minikube, etc.

    * The minimum requirements for the Solace VMR small size deployment are 2 CPUs and 8 GB memory available to the Kubernetes node.

2. Use the button below to go to the Solace Developer portal and request a Solace Community edition VMR. This process will return an email with a Download link. Download the Solace VMR image.

<a href="http://dev.solace.com/downloads/download_vmr-ce-docker" target="_blank">
    <img src="/images/register.png"/>
</a>

3. Load the Solace VMR image into a Docker container registry.

4. Create a Kubernetes Cluster

5. Deploy a Solace Deployment, (Service and Pod), onto the cluster:

    * For the following variables, substitute `<YourAdminPassword>` with the desired password for the management `admin` user. Substitute `<DockerRepo>`, `<ImageName>` and `<releaseTag>` according to your image in the container registry.

```sh
  PASSWORD=<YourAdminPassword>
  SOLACE_IMAGE_URL=<DockerRepo>.<ImageName>:<releaseTag>
```

Download and execute the following cluster create and deployment script on command line. This will create and start a small size non-HA VMR deployment with simple local non-persistent storage.
 
```sh
  wget https://raw.githubusercontent.com/SolaceProducts/solace-kubernetes-quickstart/68545/scripts/start_vmr.sh
  chmod 755 start_vmr.sh
  ./start_vmr.sh -p ${PASSWORD } -i ${SOLACE_IMAGE_URL}
```

#### Using other VMR deployment configurations

The properties of the VMR deployment are defined in the `values.yaml` file located at the `solace-kubernetes-quickstart/helm` directory which has been created as a result of running the script.

The `solace-kubernetes-quickstart/helm/values-examples` directory provides examples for `values.yaml` for several storage options:

* `small-direct-noha` (default): the simple local non-persistent storage
* `small-direct-noha-existingVolume`: to bind the PVC to an existing external volume in the network.
* `small-direct-noha-localDirectory`: to bind the PVC to a local directory on the host node.
* `small-direct-noha-provisionPvc`: to bind the PVC to a provisioned PersistentVolume (PV) in Kubernetes

To open up more service ports for external access, add now ports to the `externalPort` list in `values.yaml`. For a list of available services and default ports refer to [VMR Configuration Defaults](https://docs.solace.com/Solace-VMR-Set-Up/VMR-Configuration-Defaults.htm) in the Solace customer documentation.

It is also possible to configure the VMR deployment with more CPU and memory resources by changing the solace `size` in `values.yaml`. The Kubernetes host node resources must be also provisioned accordingly.

* `small` (default): 1.2 CPU, 6 GB memory
* `medium`: 3.5 CPU, 15 GB memory
* `large`: 7.5 CPU, 30 GB memory

Note: the deployment script installs and uses the Kubernetes `helm` tool for the deployment, which can be used to redeploy the VMR if changing deployment options. Setting permissions on the Kubernetes cluster may also be required so helm can setup and use its tiller service on the nodes. See the [Helm documentation](https://github.com/kubernetes/helm) for more details.

### Validate the Deployment

Now you can validate your deployment on command line:

```sh
prompt:~$kubectl get statefulset,services,pods,pvc
NAME                                          DESIRED   CURRENT   AGE
statefulsets/XXX-XXX-solace-kubernetes   1         1         2m
NAME                                 TYPE           CLUSTER-IP      EXTERNAL-IP      PORT(S)                                       AGE
svc/kubernetes                       ClusterIP      10.19.240.1     <none>           443/TCP                                       26m
svc/XXX-XXX-solace-kubernetes   LoadBalancer   10.19.245.131   104.154.136.44   22:31061/TCP,8080:30037/TCP,55555:31723/TCP   2m
NAME                                  READY     STATUS    RESTARTS   AGE
po/XXX-XXX-solace-kubernetes-0   1/1       Running   0          2m
NAME                                        STATUS    VOLUME                                     CAPACITY   ACCESS MODES   STORAGECLASS            AGE
pvc/data-XXX-XXX-solace-kubernetes-0   Bound     pvc-63ce3ad3-cae1-11e7-ae62-42010a800120   30Gi       RWO            XXX-XXX-standard   2


prompt:~$ kubectl describe service XXX-XXX-solace-kubernetes
Name:                     XXX-XXX-solace-kubernetes
Namespace:                default
Labels:                   app=solace-kubernetes
                          chart=solace-kubernetes-0.1.0
                          heritage=Tiller
                          release=XXX-XXX
Annotations:              <none>
Selector:                 app=solace-kubernetes,release=XXX-XXX
Type:                     LoadBalancer
IP:                       10.19.245.131
LoadBalancer Ingress:     104.154.136.44
Port:                     ssh  22/TCP
TargetPort:               22/TCP
NodePort:                 ssh  31061/TCP
Endpoints:                10.16.0.12:22
:
:
```

Note here serveral IPs and port.  In this example 104.154.136.44 is the external IP to use.

Note: when using Minikube, there is no integrated LoadBalancer. For a workaround, you can use `minikube service XXX-XXX-solace-kubernetes` to expose the service.

## Gaining admin access to the VMR

For persons used to working with Solace message router console access, this is still available with standard ssh session from any internet at port 22 by default:

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

For persons who are unfamiliar with the Solace mesage router or would prefer an administration application, the SolAdmin management application is available.  For more information on SolAdmin see the [SolAdmin page](http://dev.solace.com/tech/soladmin/).  To get SolAdmin, visit the Solace [download page](http://dev.solace.com/downloads/) and select OS version desired.  Management IP will be the Public IP associated with youe GCE instance and port will be 8080 by default.

## Testing data access to the VMR

To test data traffic though the newly created VMR instance, visit the Solace developer portal and and select your preferred programming langauge to [send and receive messages](http://dev.solace.com/get-started/send-receive-messages/). Under each language there is a Publish/Subscribe tutorial that will help you get started.

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
