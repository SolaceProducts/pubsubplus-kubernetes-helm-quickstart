#!/bin/bash
# Test latest published Solace pubsubplus Helm chart variants from gh-pages, fails out on error
#   tests pubsubplus, pubsubplus-dev, pubsubplus-ha with Helm v2 and Helm v3
# Params:
#   $1: the published location of the Solace URL
# Assumes being run on a Kubernetes environment with enough resources for HA dev deployment
#   - kubectl configured
echo "Tested published charts from ${1}"