[![Build Status](https://travis-ci.org/SolaceProducts/solace-kubernetes-quickstart.svg?branch=master)](https://travis-ci.org/SolaceProducts/solace-kubernetes-quickstart)

# Install a Solace PubSub+ Software Event Broker onto a Kubernetes cluster

## Purpose of this repository

This repository explains how to install a Solace PubSub+ Software Event Broker in various configurations onto a Kubernetes cluster. We recommend using the Helm tool for convenience, which will be described in the next sections. An [alternative method](#alternative-installation-generating-templates-for-kubernetes-kubectl-tool) using generated templates is also provided.

This guide is intended mainly for development and demo purposes. The recommended Solace PubSub+ Software Event Broker version is 9.0 or later.

This document is applicable to any platform supporting Kubernetes, with specific hints on how to set up a simple single-node MiniKube deployment on a Linux-based machine. To view examples of other platforms see:

- [Deploying a Solace PubSub+ Software Event Broker HA group onto a Google Kubernetes Engine](//github.com/SolaceProducts/solace-gke-quickstart )
- [Deploying a Solace PubSub+ Software Event Broker HA Group onto an OpenShift 3.10 or 3.11 platform](//github.com/SolaceProducts/solace-openshift-quickstart )
- Deploying a Solace PubSub+ Software Event Broker HA Group onto Amazon EKS (Amazon Elastic Container Service for Kubernetes): follow the [AWS documentation](//docs.aws.amazon.com/eks/latest/userguide/getting-started.html ) to set up EKS then this guide to deploy.
- [Install a Solace PubSub+ Software Event Broker onto a Pivotal Container Service (PKS) cluster](//github.com/SolaceProducts/solace-pks )
- Deploying a Solace PubSub+ Software Event Broker HA Group onto Azure Kubernetes Service (AKS): follow the [Azure documentation](//docs.microsoft.com/en-us/azure/aks/ ) to deploy an AKS cluster then this guide to deploy.


## Description of the Solace PubSub+ Software Event Broker

The Solace PubSub+ software event broker meets the needs of big data, cloud migration, and Internet-of-Things initiatives, and enables microservices and event-driven architecture. Capabilities include topic-based publish/subscribe, request/reply, message queues/queueing, and data streaming for IoT devices and mobile/web apps. The event broker supports open APIs and standard protocols including AMQP, JMS, MQTT, REST, and WebSocket. Moreover, it can be deployed in on-premise datacenters, natively within private and public clouds, and across complex hybrid cloud environments.

Solace PubSub+ software event brokers can be deployed in either a 3-node High-Availability (HA), or as a single node deployment. For simple test environments that need only to validate application functionality, a single instance will suffice. Note that in production, or any environment where message loss cannot be tolerated, an HA deployment is required.

## How to deploy the Solace PubSub+ Software Event Broker onto Kubernetes

In this quick start we go through the steps to set up a small-size event broker as a single stand-alone instance. If you are interested in other event broker configurations or sizes, refer to the [Deployment Configurations](#other-message-broker-deployment-configurations) section.

1. Have a Kubernetes environment

Follow your Kubernetes provider's instructions, or [here are some options](https://kubernetes.io/docs/setup/). [MiniKube](https://kubernetes.io/docs/setup/learning-environment/minikube/) is one of the popular choices to set up an environment on a local machine.

Also have the [`kubectl` tool installed](https://kubernetes.io/docs/tasks/tools/install-kubectl/) locally.

Your Kubernetes environment is ready if you get worker nodes listed and ready when running the command:
```bash
kubectl get nodes
```

This deployment assumes that a default StorageClass is available in your environment. Refer to the [**Pre-requisites section** ] for other options.
```bash
kubectl get sc | grep default
```

2. Install and configure Helm

Follow the [Helm installation guide](https://helm.sh/docs/using_helm/#installing-the-helm-client) for your platform.
On Linux a simple option to set up the latest stable release is to run:
```bash
curl -sSL https://raw.githubusercontent.com/helm/helm/master/scripts/get | bash
```

Deploy `tiller` if using default Helm v2:
```bash
# Configure Helm - enables getting started on most platforms, but grants tiller cluster-admin privileges
kubectl -n kube-system create serviceaccount tiller
kubectl create clusterrolebinding tiller --clusterrole cluster-admin --serviceaccount=kube-system:tiller
helm init --wait --service-account=tiller --upgrade # this may take some time
```

Helm is configured properly if `helm version` returns no error.

3. Install Solace PubSub+

Create a Solace PubSub+ minimum deployment with default configuration.

```bash
# Add Solace Helm charts to your local Helm repo
helm repo add solacecharts https://solacedev.github.io/solace-kubernetes-quickstart/helm-charts

# Deploy PubSub+ Standard edition, minimum footprint developer version
helm install --name my-pubsubplus-release solacecharts/pubsubplus-dev
```

This will start the deployment and provide related information and notes.

Wait for the deployment to complete, then [**check out the management and messaging services**](). Refer to the [**Troubleshooting guide**]() if any issues.

For configuration options and delete instructions, refer to the [PubSub+ Helm Chart documentation](https://github.com/SolaceDev/solace-kubernetes-quickstart/tree/HelmReorg/pubsubplus).

## Contributing

Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details on our code of conduct, and the process for submitting pull requests to us.

## Authors

See the list of [contributors](//github.com/SolaceProducts/solace-kubernetes-quickstart/graphs/contributors) who participated in this project.

## License

This project is licensed under the Apache License, Version 2.0. - See the [LICENSE](LICENSE) file for details.

## Resources

For more information about Solace technology in general please visit these resources:

- The Solace Developer Portal website at: //dev.solace.com
- Understanding [Solace technology.](//dev.solace.com/tech/)
- Ask the [Solace community](//dev.solace.com/community/).
