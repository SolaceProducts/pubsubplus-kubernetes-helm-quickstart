#!/bin/bash
#
# Licensed to the Apache Software Foundation (ASF) under one or more
# contributor license agreements.  See the NOTICE file distributed with
# this work for additional information regarding copyright ownership.
# The ASF licenses this file to You under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with
# the License.  You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# The purpose of this script is to:
#  - take a URL to a Solace PubSub+ docker container, admin password and cloud provider parameters
#  - install the required version of helm
#  - clone locally and prepare the solace chart for deployment

# Use external env variables if defined: SOLACE_KUBERNETES_QUICKSTART_REPO, SOLACE_KUBERNETES_QUICKSTART_BRANCH
# otherwise fall back to defaults (defaults are after the - (dash))
repo=${SOLACE_KUBERNETES_QUICKSTART_REPO-SolaceProducts/solace-kubernetes-quickstart}
branch=${SOLACE_KUBERNETES_QUICKSTART_BRANCH-master}
# Define if using a service account, e.g. for automation
echo "`date` INFO: Using repo=${repo}, branch=${branch}"

# Initialize our own variables:
cloud_provider="undefined"  # recognized other options are "gcp" or "aws"
solace_password=""
solace_image="solace/solace-pubsub-standard:latest"
values_file="values-examples/dev100-direct-noha.yaml"
verbose=0

# Read options
OPTIND=1         # Reset in case getopts has been used previously in the shell.
while getopts "c:i:p:v:" opt; do
    case "$opt" in
    c)  cloud_provider=$OPTARG   # optional but default will not work in all env
        ;;
    i)  solace_image=$OPTARG     # optional
        ;;
    p)  solace_password=$OPTARG
        ;;
    v)  values_file=$OPTARG      # optional
        ;;
    esac
done

shift $((OPTIND-1))
[ "$1" = "--" ] && shift

verbose=1
echo "`date` INFO: solace_image=${solace_image}, cloud_provider=${cloud_provider}, values_file=${values_file} Leftovers: $@"

# kubectl installed is a pre-requisite
exists()
{
  command -v "$1" >/dev/null 2>&1
}
if exists kubectl; then
  echo 'kubectl exists!'
else
  echo 'kubectl not found on the PATH'
  echo '	Please install kubectl (see https://kubernetes.io/docs/tasks/tools/install-kubectl/)'
  echo '	Or if you have already installed it, add it to the PATH shell variable'
  echo "	Current PATH: ${PATH}"
  exit -1
fi

# Ensure helm is installed
os_type=`uname`
case ${os_type} in 
  "Darwin" )
    helm_type="darwin-amd64"
    helm_version="v2.9.1"
    archive_extension="tar.gz"
    sed_options="-E -i.bak"
    sudo_command="sudo"
    ;;
  "Linux" )
    helm_type="linux-amd64"
    helm_version="v2.9.1"
    archive_extension="tar.gz"
    sed_options="-i.bak"
    sudo_command="sudo"
    ;;
  *_NT* ) # BASH emulation on windows
    helm_type="windows-amd64"
    helm_version=v2.9.1
    archive_extension="zip"
    sed_options="-i.bak"
    sudo_command=""
    ;;
esac
if exists helm; then
  echo "`date` INFO: Found helm $(helm version --client --short)"
else
  pushd /tmp
  curl -O https://storage.googleapis.com/kubernetes-helm/helm-${helm_version}-${helm_type}.${archive_extension}
  tar zxf helm-${helm_version}-${helm_type}.${archive_extension} || unzip helm-${helm_version}-${helm_type}.${archive_extension}
  ${sudo_command} mv ${helm_type}/helm* /usr/bin
  popd
  echo "`date` INFO: Installed helm $(helm version --client --short)"
fi

# Deploy tiller
## possible other option but then need to deal with installed helm : if [[ `helm init | grep "Tiller is already installed"` ]] ; then
if timeout 5s helm version --server --short >/dev/null 2>&1; then
  tiller_already_deployed=true
  echo "`date` INFO: Found tiller on server, using $(helm version --server --short)"
else
  tiller_already_deployed=
  # Need to init helm to deploy tiller
  if [[ $(kubectl version | grep Server | grep 'GitVersion:\"v1.6.') ]]; then
    # For kubernetes v6
    helm init
  else
    # For kubernetes >=v7
    kubectl create serviceaccount --namespace kube-system tiller
    # Requires account/service account to have add-iam-policy-binding to "roles/container.admin"
    kubectl create clusterrolebinding tiller-cluster-rule --clusterrole=cluster-admin --serviceaccount=kube-system:tiller
    helm init --service-account tiller
  fi
fi

# Clone the solace-kubernetes-quickstart project if needed
scriptpath="$( cd "$(dirname "$0")" ; pwd -P )"
if [[ $(echo "${scriptpath}" | grep "solace-kubernetes-quickstart/scripts") ]]; then
  echo "`date` INFO: Found solace-kubernetes-quickstart project already cloned"
else
  echo "`date` INFO: Cloning the solace-kubernetes-quickstart repo"
  git clone --branch $branch https://github.com/$repo
  cd solace-kubernetes-quickstart
  cd solace
fi

# Ensure current dir is within the chart - e.g solace-kubernetes-quickstart/solace
if [ ! -d "templates" ]; then
  echo "`date` INFO: Must be in the chart directory, exiting. Current dir is $(pwd)."
  exit -1
fi
echo "`date` INFO: Building helm charts"
cp ${values_file} ./values.yaml
IFS=':' read -ra container_array <<< "$solace_image"
sed ${sed_options} "s:SOLOS_IMAGE_REPO:${container_array[0]}:g" values.yaml
tag=${container_array[1]-latest}   # default to latest if no tag provided
sed ${sed_options} "s:SOLOS_IMAGE_TAG:${tag}:g"  values.yaml
sed ${sed_options} "s/SOLOS_CLOUD_PROVIDER/${cloud_provider}/g"  values.yaml
sed ${sed_options} "s/SOLOS_ADMIN_PASSWORD/${solace_password}/g" templates/secret.yaml
rm templates/secret.yaml.bak

# Wait until helm tiller is up and ready to proceed
#  workaround until https://github.com/kubernetes/helm/issues/2114 resolved
if [[ -z "$tiller_already_deployed" ]] ; then
  kubectl rollout status -w deployment/tiller-deploy --namespace=kube-system
fi

echo "`date` INFO: READY TO DEPLOY Solace PubSub+ TO CLUSTER"
echo "#############################################################"
echo "Next steps to complete the deployment:"
if [[ "$(pwd)" != *solace-kubernetes-quickstart/solace ]]; then
  echo "cd solace-kubernetes-quickstart/solace  # replace with the path to your chart"
fi
echo "helm install . -f values.yaml"
echo "watch kubectl get pods --show-labels"

