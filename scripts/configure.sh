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

# use external env variables if defined: SOLACE_KUBERNETES_QUICKSTART_REPO, SOLACE_KUBERNETES_QUICKSTART_BRANCH
# otherwise fall back to defaults (defaults are after the - (dash))
repo=${SOLACE_KUBERNETES_QUICKSTART_REPO-SolaceProducts/solace-kubernetes-quickstart}
branch=${SOLACE_KUBERNETES_QUICKSTART_BRANCH-master}
# Define if using a service account, e.g. for automation
kubectl_create_clusterrolebinding_credentials=${SOLACE_KUBERNETES_QUICKSTART_CLUSTERROLEBINDING_CREDENTIALS}
echo "`date` INFO: Using repo=${repo}, branch=${branch}, kubectl_create_clusterrolebinding_credentials=${kubectl_create_clusterrolebinding_credentials}"

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
OPTIND=1         # Reset in case getopts has been used previously in the shell.

# Initialize our own variables:
cloud_provider="undefined"  # recognized other options are "gcp" or "aws"
solace_password=""
solace_image=""
values_file="values-examples/dev100-direct-noha.yaml"
verbose=0

while getopts "c:i:p:v:" opt; do
    case "$opt" in
    c)  cloud_provider=$OPTARG
        ;;
    i)  solace_image=$OPTARG
        ;;
    p)  solace_password=$OPTARG
        ;;
    v)  values_file=$OPTARG
        ;;
    esac
done

shift $((OPTIND-1))
[ "$1" = "--" ] && shift

verbose=1
echo "`date` INFO: solace_image=${solace_image}, cloud_provider=${cloud_provider}, values_file=${values_file} Leftovers: $@"

os_type=`uname`
case ${os_type} in 
  "Darwin" )
    helm_type="darwin-amd64"
    helm_version="v2.7.2"
    archive_extension="tar.gz"
    sed_options="-E -i.bak"
    ;;
  "Linux" )
    helm_type="linux-amd64"
    helm_version="v2.7.2"
    archive_extension="tar.gz"
    sed_options="-i.bak"
    ;;
  *_NT* ) # BASH emulation on windows
    helm_type="windows-amd64"
    helm_version=v2.9.1
    archive_extension="zip"
    sed_options="-i.bak"
    ;;
esac
echo "`date` INFO: DOWNLOAD AND DEPLOY HELM"
echo "#############################################################"
curl -O https://storage.googleapis.com/kubernetes-helm/helm-${helm_version}-${helm_type}.${archive_extension}
tar zxf helm-${helm_version}-${helm_type}.${archive_extension} || unzip helm-${helm_version}-${helm_type}.${archive_extension}
mv ${helm_type} helm
export HELM="`pwd`/helm/helm"

# [TODO] Need proper way to set service account for tiller
if [ "$cloud_provider" == "gcp" ]
then
  kubectl create serviceaccount --namespace kube-system tiller
  kubectl $kubectl_create_clusterrolebinding_credentials create clusterrolebinding tiller-cluster-rule --clusterrole=cluster-admin --serviceaccount=kube-system:tiller
  "$HELM" init --service-account tiller
else
  "$HELM" init
fi

# While helm is busy initializing prepare the solace helm chart
echo "`date` INFO: CLONE THE solace-kubernetes-quickstart REPO"
echo "#############################################################"
git clone --branch $branch https://github.com/$repo
cd solace-kubernetes-quickstart
cd solace

echo "`date` INFO: BUILD HELM CHARTS"
cp ${values_file} ./values.yaml
IFS=':' read -ra container_array <<< "$solace_image"
sed ${sed_options} "s:SOLOS_IMAGE_REPO:${container_array[0]}:g" values.yaml
sed ${sed_options} "s:SOLOS_IMAGE_TAG:${container_array[1]}:g"  values.yaml
sed ${sed_options} "s/SOLOS_CLOUD_PROVIDER/${cloud_provider}/g"  values.yaml
sed ${sed_options} "s/SOLOS_ADMIN_PASSWORD/${solace_password}/g" templates/secret.yaml
rm templates/secret.yaml.bak

# Wait until helm tiller is up and ready to proceed
#  workaround until https://github.com/kubernetes/helm/issues/2114 resolved
kubectl rollout status -w deployment/tiller-deploy --namespace=kube-system

echo "`date` INFO: READY TO DEPLOY Solace PubSub+ TO CLUSTER"
echo "#############################################################"
echo "Next steps to complete the deployment:"
echo "cd solace-kubernetes-quickstart/solace"
echo "../../helm/helm install . -f values.yaml"
echo "kubectl get statefulsets,services,pods,pvc,pv"

