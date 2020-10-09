#!/bin/bash
# Create pubsubplus Helm chart variants for HA, Dev and non-HA purposes and package them
# Assumes being run from quickstart project root and script will fail if defaults/clues to customize changed
#  - assuming Chart.yaml default is pubsubplus, the non-HA version of the pubsubplus Helm chart
#  - assuming values.yaml defaults solace.redundancy=false, solace.size-prod*, storage.size=*Gi

# Customize pubsubplus-ha
cp -r pubsubplus/ pubsubplus-ha/
sed -i 's/description:.*$/description: Deploy an HA redundancy group of Solace PubSub+ Event Broker Software onto a Kubernetes Cluster/g' pubsubplus-ha/Chart.yaml
sed -i '/name:/ s/pubsubplus/pubsubplus-ha/g' pubsubplus-ha/Chart.yaml
# no need to update solace.size and storage.size
sed -i 's/redundancy:.*$/redundancy: true/g' pubsubplus-ha/values.yaml
sed -i 's/This chart bootstraps a single-node or HA deployment$/This chart bootstraps an HA redundancy group deployment/g' pubsubplus-ha/README.md
sed -i 's@solacecharts/pubsubplus@solacecharts/pubsubplus-ha@g' pubsubplus-ha/README.md
sed -i '/`solace.redundancy`/ s/`false`/`true`/g' pubsubplus-ha/README.md
helm package pubsubplus-ha

# Customize pubsubplus-dev
cp -r pubsubplus/ pubsubplus-dev/
sed -i 's/description:.*$/description: Deploy a single-node non-HA Solace PubSub+ Event Broker Software onto a Kubernetes Cluster for development purposes/g' pubsubplus-dev/Chart.yaml
sed -i '/name:/ s/pubsubplus/pubsubplus-dev/g' pubsubplus-dev/Chart.yaml
sed -i 's/size: prod.*$/size: dev/g' pubsubplus-dev/values.yaml
sed -i 's/size: .*Gi/size: 10Gi/g' pubsubplus-dev/values.yaml
sed -i 's/# Solace PubSub+ Message Broker Helm Chart/# Solace PubSub+ Message Broker Helm Chart for Developers/g' pubsubplus-dev/README.md
sed -i 's/This chart bootstraps a single-node or HA deployment$/This chart bootstraps single-node deployment for Developers/g' pubsubplus-dev/README.md
sed -i 's@solacecharts/pubsubplus@solacecharts/pubsubplus-dev@g' pubsubplus-dev/README.md
sed -i '/`solace.size`/ s/| `prod.*` |/| `dev` |/g' pubsubplus-dev/README.md
sed -i '/`storage.size`/ s/| `..Gi` |/| `10Gi` |/g' pubsubplus-dev/README.md
helm package pubsubplus-dev

# Customize pubsubplus
# no need to update Chart.yaml name
sed -i 's/description:.*$/description: Deploy a single-node non-HA Solace PubSub+ Event Broker Software onto a Kubernetes Cluster/g' pubsubplus/Chart.yaml
# no need to update values.yaml solace.redundancy, solace.size and storage.size
sed -i 's/This chart bootstraps a single-node or HA deployment$/This chart bootstraps a single-node deployment/g' pubsubplus/README.md
helm package pubsubplus
