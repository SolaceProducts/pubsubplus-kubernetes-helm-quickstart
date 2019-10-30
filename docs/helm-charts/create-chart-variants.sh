#!/bin/bash
# Create pubsubplus Helm chart variants for HA, Dev and non-HA purposes and package them
# Assumes being run from quickstart project root and script will fail if defaults/clues to customize changed
#  - assuming Chart.yaml default is pubsubplus, the non-HA version of the pubsubplus Helm chart
#  - assuming values.yaml defaults solace.redundancy=false, solace.size-prod*, storage.size=*Gi

# Customize pubsubplus-ha
cp -r pubsubplus/ pubsubplus-ha/
sed -i 's/description:.*$/description: Deploy an HA redundancy group of Solace PubSub+ software event broker onto a Kubernetes Cluster/g' pubsubplus-ha/Chart.yaml
sed -i '/name:/ s/pubsubplus/pubsubplus-ha/g' pubsubplus-ha/Chart.yaml
# no need to update values.yaml solace.size and storage.size
sed -i 's/redundancy:.*$/redundancy: true/g' pubsubplus-ha/values.yaml
helm package pubsubplus-ha

# Customize pubsubplus-dev
cp -r pubsubplus/ pubsubplus-dev/
sed -i 's/description:.*$/description: Deploy a minimum footprint non-HA Solace PubSub+ software event broker onto a Kubernetes Cluster for development purposes/g' pubsubplus-dev/Chart.yaml
sed -i '/name:/ s/pubsubplus/pubsubplus-dev/g' pubsubplus-dev/Chart.yaml
sed -i 's/size: prod.*$/size: dev/g' pubsubplus-dev/values.yaml
sed -i 's/size: .*Gi/size: 10Gi/g' pubsubplus-dev/values.yaml
helm package pubsubplus-dev

# Customize pubsubplus
# no need to update Chart.yaml name
sed -i 's/description:.*$/description: Deploy a single-node non-HA Solace PubSub+ software event broker onto a Kubernetes Cluster/g' pubsubplus/Chart.yaml
# no need to update values.yaml solace.redundancy, solace.size and storage.size
helm package pubsubplus
