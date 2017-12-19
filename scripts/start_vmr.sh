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
#  - take a URL to a Solace VMR docker container
#  - validate the container against known MD5
#  - load the container to create a local instance
#  - upload the instance into google container registery
#  - clean up load docker


OPTIND=1         # Reset in case getopts has been used previously in the shell.

# Initialize our own variables:
solace_password=""
solace_image=""
values_file="values-examples/small-direct-noha.yaml"
verbose=0

while getopts "i:p:v:" opt; do
    case "$opt" in
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
echo "`date` INFO: solace_image=${solace_image}, values_file=${values_file} Leftovers: $@"

# [TODO] Need proper way to set service account for tiller
#kubectl create serviceaccount --namespace kube-system tiller
#kubectl create clusterrolebinding tiller-cluster-rule --clusterrole=cluster-admin --serviceaccount=kube-system:tiller
#kubectl edit deploy --namespace kube-system tiller-deploy #and add the line serviceAccount: tiller to spec/template/spec

helm_version=v2.7.2
os_type=`uname`

case ${os_type} in 
  "Darwin" )
    helm_type="darwin-amd64"
    sed_options="-iE"
    ;;
  "Linux" )
    helm_type="linux-amd64"
    sed_options="-i"
    ;;
esac

echo "`date` INFO: DOWNLOAD HELM"
echo "#############################################################"
wget https://storage.googleapis.com/kubernetes-helm/helm-${helm_version}-${helm_type}.tar.gz
tar zxf helm-${helm_version}-${helm_type}.tar.gz
mv ${helm_type} helm
export PATH=$PATH:~/helm
helm init

echo "`date` INFO: BUILD HELM CHARTS"
echo "#############################################################"
git clone https://github.com/SolaceProducts/solace-kubernetes-quickstart
cd solace-kubernetes-quickstart
#[TODO] Remove this line once HA is promoted to master
git checkout SOL-1244
cd solace

cp ${values_file} ./values.yaml

IFS=':' read -ra container_array <<< "$solace_image"
sed ${sed_options} "s:SOLOS_IMAGE_REPO:${container_array[0]}:g" values.yaml
sed ${sed_options} "s:SOLOS_IMAGE_TAG:${container_array[1]}:g"  values.yaml
sed ${sed_options} "s/SOLOS_ADMIN_PASSWORD/${solace_password}/g" templates/pre-install-secret.yaml

echo "`date` INFO: DEPLOY VMR TO CLUSTER"
echo "#############################################################"
# Ensure helm tiller is up and ready to accept a release then proceed
#  workaround until https://github.com/kubernetes/helm/issues/2114 resolved
kubectl rollout status -w deployment/tiller-deploy --namespace=kube-system
helm install . -f values.yaml

echo "`date` INFO: DEPLOY VMR COMPLETE"
echo "#############################################################"
echo "`date` INFO: View status with 'kubectl get statefulset,svc,pods,pvc,pv'"


