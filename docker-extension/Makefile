REPOSITORY = localhost:5001
IMAGE?=$(REPOSITORY)/educates-docker-extension
TAG?=latest

BUILDER=buildx-multi-arch

INFO_COLOR = \033[0;36m
NO_COLOR   = \033[m
DEV_UI_SOURCE?=http://localhost:3000

build-extension: ## Build service image to be deployed as a desktop extension
	docker build --build-arg REPOSITORY=$(REPOSITORY) --build-arg TAG=$(TAG) --tag=$(IMAGE):$(TAG) .

install-extension: build-extension ## Install the extension
	docker extension install --force $(IMAGE):$(TAG)

update-extension: build-extension ## Update the extension
	docker extension update --force $(IMAGE):$(TAG)

.PHONY: debug
debug: ## Enable debug in the extension
	docker extension dev debug $(IMAGE):$(TAG)

.PHONY: source
source: ## Replace the UI source of the extension
	docker extension dev ui-source $(IMAGE):$(TAG) $(DEV_UI_SOURCE)

.PHONY: dev-enable
dev-enable: source debug

.PHONY: dev-reset
dev-reset: ## Reset development status of the extension
	docker extension dev reset $(IMAGE):$(TAG)

help: ## Show this help
	@echo Please specify a build target. The choices are:
	@grep -E '^[0-9a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "$(INFO_COLOR)%-30s$(NO_COLOR) %s\n", $$1, $$2}'

.PHONY: help
