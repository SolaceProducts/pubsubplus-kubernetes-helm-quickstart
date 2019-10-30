#!/bin/bash
# Create pubsubplus Helm chart variants for HA, Dev and non-HA purposes and package them
# Assumes being run from quickstart project root and script will fail if clues to customize changed 

# Customize pubsubplus-ha
cp -r pubsubplus/ pubsubplus-ha/
sed -i 's/description:.*$/description: Deploy an HA redundancy group of Solace PubSub+ software event broker onto a Kubernetes Cluster/g' pubsubplus-ha/Chart.yaml
sed -i '/name:/ s/pubsubplus/pubsubplus-ha/g' pubsubplus-ha/Chart.yaml
helm package pubsubplus-ha

# Customize pubsubplus-dev
cp -r pubsubplus/ pubsubplus-dev/
sed -i 's/description:.*$/description: Deploy a minimum footprint non-HA Solace PubSub+ software event broker onto a Kubernetes Cluster for development purposes/g' pubsubplus-dev/Chart.yaml
sed -i '/name:/ s/pubsubplus/pubsubplus-dev/g' pubsubplus-dev/Chart.yaml
helm package pubsubplus-dev

# Customize pubsubplus
sed -i 's/description:.*$/description: Deploy a single-node non-HA Solace PubSub+ software event broker onto a Kubernetes Cluster/g' pubsubplus/Chart.yaml
helm package pubsubplus
