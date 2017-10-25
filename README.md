# Install a Solace Message Router onto a Kubernetes cluster

## Purpose of this repository

This repository explaines, in general terms, how to install a Solace VMR onto a Kubernetes cluster.  To view examples of specific enviroments see:

- [Installing Solace VMR on Google Compute Engine](https://github.com/SolaceProducts/solace-gke-quickstart)

## Description of Solace VMR

The Solace Virtual Message Router (VMR) provides enterprise-grade messaging capabilities deployable in any computing environment. The VMR provides the same rich feature set as Solace’s proven hardware appliances, with the same open protocol support, APIs and common management. The VMR can be deployed in the datacenter or natively within all popular private and public clouds.

## How to Deploy a VMR onto Kubernetes

This is a 5 step process:

1. Perform any pre-requisites to run Kubernetes in your target enviroment.  This can be things like create GCP project, install miniKube, etc.

1. Register and recieve an link to Solace VMR Docker Image.

1. Load the Solace VMR image into a Docker registry.

1. Create a Kubernetes Cluster

1. Deploy a Solace Deployment, (Service and Pod), onto the cluster.

- Download and execute the clustre create and deployment script in the google cloud shell.  Replace ??? with the release tag of the image in the container registry.

```Shell
PASSWORD=<YourAdminPassword>
SOLACE_IMAGE_URL=<DockerRepo>.<ImageName>:<releaseTag>

wget https://raw.githubusercontent.com/SolaceProducts/solace-kubernetes-quickstart/68545/scripts/start_vmr.sh
chmod 755 start_vmr.sh
./start_vmr.sh -p ${PASSWORD } -i ${SOLACE_IMAGE_URL}
```

- Now you can validate you deployment, in the google cloud shell:

```sh
prompt:~$ kubectl get deployment,svc,pods,pvc

NAME            DESIRED   CURRENT   UP-TO-DATE   AVAILABLE   AGE
deploy/solace   1         1         1            1           1h
NAME             CLUSTER-IP     EXTERNAL-IP      PORT(S)     AGE
svc/kubernetes   XX.XX.XX.XX    <none>           443/TCP     18h
svc/solace       10.15.250.74   104.154.54.154   80:31918/TCP,8080:31910/TCP,2222:31020/TCP,55555:32120/TCP,1883:32061/TCP   1h
NAME                         READY     STATUS    RESTARTS   AGE
po/solace-2554909293-tgqmk   1/1       Running   0          1h
NAME       STATUS    VOLUME                                     CAPACITY   ACCESSMODES   STORAGECLASS   AGE
pvc/dshm   Bound     pvc-5cb52cd8-b408-11e7-a882-42010af001ea   1Gi        RWO           standard       1h

prompt:~$ kubectl describe service solace
Name:                   solace
Namespace:              default
Labels:                 io.kompose.service=solace
Annotations:            kompose.cmd=./kompose -f solace-compose.yaml up
                        kompose.service.type=LoadBalancer
                        kompose.version=
Selector:               io.kompose.service=solace
Type:                   LoadBalancer
IP:                     10.15.250.74
LoadBalancer Ingress:   104.154.54.154
Port:                   80      80/TCP
NodePort:               80      31918/TCP
:
:
```

Note here serveral IPs and port.  In this example 104.154.54.154 is the external IP to use.

## Gaining admin access to the VMR

For persons used to working with Solace message router console access, this is still available with standard ssh session from any internet:

![alt text](https://raw.githubusercontent.com/SolaceProducts/solace-gke-quickstart/68545/images/solace_console.png "SolOS CLI")

For persons who are unfamiliar with the Solace mesage router or would prefer an administration application the SolAdmin management application is available.  For more information on SolAdmin see the [SolAdmin page](http://dev.solace.com/tech/soladmin/).  To get SolAdmin, visit the Solace [download page](http://dev.solace.com/downloads/) and select OS version desired.  Management IP will be the Public IP associated with youe GCE instance and port will be 8080 by default.

![alt text](https://raw.githubusercontent.com/SolaceProducts/solace-kubernetes-quickstart/68545/images/gce_soladmin.png "soladmin connection to gce")

## Testing data access to the VMR

To test data traffic though the newly created VMR instance, visit the Solace developer portal and and select your preferred programming langauge to [send and receive messages](http://dev.solace.com/get-started/send-receive-messages/). Under each language there is a Publish/Subscribe tutorial that will help you get started.

![alt text](https://raw.githubusercontent.com/SolaceProducts/solace-kubernetes-quickstart/68545/images/solace_tutorial.png "getting started publish/subscribe")

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
