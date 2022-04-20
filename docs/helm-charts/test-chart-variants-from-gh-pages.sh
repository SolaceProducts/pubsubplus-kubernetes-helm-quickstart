#!/bin/bash
# Test latest published Solace pubsubplus Helm chart variants from gh-pages, fails out on error
#   tests pubsubplus, pubsubplus-dev, pubsubplus-ha with Helm v2 and Helm v3
# Params:
#   $1: the published location of the Solace URL
#   $2: k8s cluster size, default is dev: barely enough place for a dev HA deployment
# Assumes being run on a Kubernetes environment with enough resources for HA dev deployment
#   - kubectl configured
echo "Testing published charts from ${1}"
kubectl get nodes -o wide


testDeployHelmv2 () {
  # Params: $1 is the Helm chart name
  echo
  helm install --name my-release solacecharts/$1 --set solace.size=dev
  echo
  echo "Waiting for chart $1 to deploy..."
  echo
  until kubectl get pods --show-labels | grep my-release-$1 | grep -m 1 -E 'active=true'; do sleep 10; done
  sleep 5
  echo -e "\nProtocol\tAddress\n"`kubectl get svc --namespace default my-release-$1 -o jsonpath="{range .spec.ports[*]}{.name}\tmy-release-$1.default.svc.cluster.local:{.port}\n"`
  helm delete my-release --purge
  kubectl delete pvc --all
  echo "PASSED: Tested chart $1 using Helm v2"
}

testDeployHelmv3 () {
  # Params: $1 is the Helm chart name
  echo "============================================================================"
  helm install my-release solacecharts/$1 --set solace.size=dev
  echo
  echo "Waiting for chart $1 to deploy..."
  echo
  until kubectl get pods --show-labels | grep my-release-$1 | grep -m 1 -E 'active=true'; do sleep 10; done
  sleep 5
  echo -e "\nProtocol\tAddress\n"`kubectl get svc --namespace default my-release-$1 -o jsonpath="{range .spec.ports[*]}{.name}\tmy-release-$1.default.svc.cluster.local:{.port}\n"`
  helm delete my-release
  kubectl delete pvc --all
  echo "PASSED: Tested chart $1 using Helm v3"
}

# reset Helm
helm reset --force || echo "Tried helm reset"
rm -rf ~/.helm || echo "Tried rm .helm"
sudo rm /usr/local/bin/helm


# install Helm v2
curl -sSL https://raw.githubusercontent.com/helm/helm/master/scripts/get | bash
# This enables getting started on most platforms by granting Tiller cluster-admin privileges
kubectl -n kube-system create serviceaccount tiller
kubectl create clusterrolebinding tiller --clusterrole cluster-admin --serviceaccount=kube-system:tiller
helm init --wait --service-account=tiller --upgrade # this may take some time
helm version

# test charts
helm repo add solacecharts https://solaceproducts.github.io/pubsubplus-kubernetes-quickstart/helm-charts
helm repo list

testDeployHelmv2 pubsubplus-dev
testDeployHelmv2 pubsubplus
testDeployHelmv2 pubsubplus-ha

# cleanup
helm reset --force
rm -rf ~/.helm
sudo rm /usr/local/bin/helm

sleep 5

# install Helm v3
curl https://raw.githubusercontent.com/helm/helm/master/scripts/get-helm-3 | bash
helm version

# test charts
helm repo add solacecharts https://solaceproducts.github.io/pubsubplus-kubernetes-quickstart/helm-charts
helm repo list

testDeployHelmv3 pubsubplus-dev
testDeployHelmv3 pubsubplus
testDeployHelmv3 pubsubplus-ha

exit 0
