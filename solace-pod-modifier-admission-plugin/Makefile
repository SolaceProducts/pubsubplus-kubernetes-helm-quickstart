# Setting SHELL to bash allows bash commands to be executed by recipes.
# This is a requirement for 'setup-envtest.sh' in the test target.
# Options are set to exit when a recipe line exits non-zero or a piped command fails.
SHELL = /usr/bin/env bash -o pipefail
.SHELLFLAGS = -ec

# Get the currently used golang install path (in GOPATH/bin, unless GOBIN is set)
ifeq (,$(shell go env GOBIN))
GOBIN=$(shell go env GOPATH)/bin
else
GOBIN=$(shell go env GOBIN)
endif

# Tools for deploy
KUBECTL?=kubectl  # Use `oc` for OpenShift
#KUBECTL?=oc
CONTAINER_TOOL?=docker  # `podman` if alternative
#CONTAINER_TOOL?=podman
KUSTOMIZE?=$(shell pwd)/bin/kustomize

# No default for image
IMAGE ?= $(error IMAGE not defined, please set IMAGE=<container-image-refernce>)

all: build
.PHONY: all

##@ General

# The help target prints out all targets with their descriptions organized
# beneath their categories. The categories are represented by '##@' and the
# target descriptions by '##'. The awk commands is responsible for reading the
# entire set of makefiles included in this invocation, looking for lines of the
# file as xyz: ## something, and then pretty-format the target and help. Then,
# if there's a line with ##@ something, that gets pretty-printed as a category.
# More info on the usage of ANSI control characters for terminal formatting:
# https://en.wikipedia.org/wiki/ANSI_escape_code#SGR_parameters
# More info on the awk command:
# http://linuxcommand.org/lc3_adv_awk.php

.PHONY: help
help: ## Display this help
	@awk 'BEGIN {FS = ":.*##"; printf "\nUsage:\n  make \033[36m<target>\033[0m\n"} /^[a-zA-Z_0-9-]+:.*?##/ { printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2 } /^##@/ { printf "\n\033[1m%s\033[0m\n", substr($$0, 5) } ' $(MAKEFILE_LIST)

##@ Development

.PHONY: fmt
fmt: ## Run go fmt against code
	go fmt ./...

.PHONY: vet
vet: ## Run go vet against code
	go vet ./...

##@ Build

.PHONY: build
build: fmt vet ## Build binary
	go build -o bin/pod-modifier ./cmd/

.PHONY: image-build
image-build: build ## Build container image
	$(CONTAINER_TOOL) build -t ${IMAGE} .

.PHONY: image-push
image-push: ## Push container image
	$(CONTAINER_TOOL) push ${IMAGE}

##@ Deployment

.PHONY: deploy
deploy: ## Deploy Solace pod-modifier mutating admission webhook including related artifacts
	cp deploy/kustomization.yaml deploy/kustomization.yaml.tmp
	cd deploy && $(KUSTOMIZE) edit set image pod-modifier=$(IMAGE)
	$(KUSTOMIZE) build deploy | $(KUBECTL) apply -f -
	mv deploy/kustomization.yaml.tmp deploy/kustomization.yaml

.PHONY: undeploy
undeploy: ## Undeploy webhook including related artifacts
	$(KUSTOMIZE) build deploy | $(KUBECTL) delete --ignore-not-found -f -

.PHONY: setup-kustomize
setup-kustomize: ## Download and setup Kustomize tool locally if missing
# Refer to https://kubectl.docs.kubernetes.io/installation/kustomize/binaries/ - script does not work for ARM architecture
	(if ! test -f $(KUSTOMIZE); then cd bin && curl -s "https://raw.githubusercontent.com/kubernetes-sigs/kustomize/master/hack/install_kustomize.sh" | bash; fi)
