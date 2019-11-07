## Solace PubSub+ Event Broker Alternative installation: generating templates for Kubernetes Kubectl tool

This is for users not wishing to install the Helm server-side Tiller on the Kubernetes cluster.

This method will first generate installable Kubernetes templates from this project's Helm charts, then the templates can be installed using the `kubectl` tool.
Note that Helm will not be able to manage your Kubernetes rollouts lifecycle.

The templates will be generated using Helm v2 client as a templating engine only, with no Tiller deployed.


### Step 1: Generate Kubernetes templates for Solace message broker deployment

1) Clone this project:

```sh
git clone https://github.com/SolaceProducts/solace-kubernetes-quickstart.git
cd solace-kubernetes-quickstart # This directory will be referenced as <project-root>
```

2) [Download](//github.com/helm/helm/releases/tag/v2.9.1 ) and install the Helm client locally.

We will assume that it has been installed to the `<project-root>/bin` directory.

3) Customize the Solace chart for your deployment

The Solace chart includes raw Kubernetes templates and a "values.yaml" file to customize them when the templates are generated.

The chart is located in the `solace` directory:

`cd <project-root>/solace`

a) Optionally replace the `<project-root>/solace/values.yaml` file with one of the prepared examples from the `<project-root>/solace/values-examples` directory. For details refer to the [Other Deployment Configurations section](#other-message-broker-deployment-configurations) in this document.

b) Then edit `<project-root>/solace/values.yaml` and replace following parameters:

SOLOS_CLOUD_PROVIDER: Current options are "gcp" or "aws" or leave it unchanged for unknown (note: specifying the provider will optimize volume provisioning for supported providers).
<br/>
SOLOS_IMAGE_REPO and SOLOS_IMAGE_TAG: use `solace/solace-pubsub-standard` and `latest` for the latest available or specify a [version from DockerHub](//hub.docker.com/r/solace/solace-pubsub-standard/tags/ ). For more options, refer to the [Solace PubSub+ message broker docker image section](#step-3-optional) in this document. 

c) Configure the Solace management password for `admin` user in `<project-root>/solace/templates/secret.yaml`:

SOLOS_ADMIN_PASSWORD: change it to the desired password, considering the [password rules](//docs.solace.com/Configuring-and-Managing/Configuring-Internal-CLI-User-Accounts.htm#Changing-CLI-User-Passwords ).

4) Generate the templates

```sh
cd <project-root>/solace
# Create location for the generated templates
mkdir generated-templates
# In next command replace myrelease to the desired release name
<project-root>/bin/helm template --name myrelease --values values.yaml --output-dir ./generated-templates .
```

The generated set of templates are now available in the `<project-root>/solace/generated-templates` directory.

### Step 2: Deploy the templates on the target system

Assumptions: `kubectl` is deployed and configured to point to your Kubernetes cluster

1) Optionally copy the `generated-templates` directory with contents if this is on a different host

2) Assign rights to current user to modify cluster-wide RBAC (required for creating clusterrole binding when deploying the Solace template podModRbac.yaml)

Example:

```sh
# Get current user - GCP example. Returns e.g.: myname@example.org
gcloud info | grep Account  
# Assign rigths - replace user
kubectl create clusterrolebinding myname-cluster-admin-binding \
  --clusterrole=cluster-admin \
  --user=myname@example.org
```

3) Initiate the deployment:

`kubectl apply --recursive -f ./generated-templates/solace`

Wait for the deployment to complete, which is then ready to use.

4) To delete deployment, execute:

`kubectl delete --recursive -f ./generated-templates/solace`

