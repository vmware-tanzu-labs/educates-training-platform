IMAGE_REPOSITORY = localhost:5001
PACKAGE_VERSION = latest
RELEASE_VERSION = 0.0.1

UNAME_SYSTEM := $(shell uname -s)
UNAME_MACHINE := $(shell uname -m)

DOCKER_PLATFORM = linux/amd64

ifeq ($(UNAME_SYSTEM),Darwin)
ifeq ($(UNAME_MACHINE),arm64)
DOCKER_PLATFORM = linux/arm64
endif
endif

all: push-all-images deploy-cluster-essentials deploy-training-platform deploy-workshop

build-all-images: build-session-manager build-training-portal \
  build-base-environment build-jdk8-environment build-jdk11-environment \
  build-jdk17-environment build-conda-environment build-docker-registry \
  build-pause-container build-secrets-manager

push-all-images: push-session-manager push-training-portal \
  push-base-environment push-jdk8-environment push-jdk11-environment \
  push-jdk17-environment push-conda-environment push-docker-registry \
  push-pause-container push-secrets-manager

build-core-images: build-session-manager build-training-portal \
  build-base-environment build-docker-registry build-pause-container \
  build-secrets-manager

push-core-images: push-session-manager push-training-portal \
  push-base-environment push-docker-registry push-pause-container \
  push-secrets-manager

build-session-manager:
	docker build --platform $(DOCKER_PLATFORM) -t $(IMAGE_REPOSITORY)/educates-session-manager:$(PACKAGE_VERSION) session-manager

push-session-manager: build-session-manager
	docker push $(IMAGE_REPOSITORY)/educates-session-manager:$(PACKAGE_VERSION)

build-training-portal:
	docker build --platform $(DOCKER_PLATFORM) -t $(IMAGE_REPOSITORY)/educates-training-portal:$(PACKAGE_VERSION) training-portal

push-training-portal: build-training-portal
	docker push $(IMAGE_REPOSITORY)/educates-training-portal:$(PACKAGE_VERSION)

build-base-environment:
	docker build --platform $(DOCKER_PLATFORM) -t $(IMAGE_REPOSITORY)/educates-base-environment:$(PACKAGE_VERSION) workshop-images/base-environment

push-base-environment: build-base-environment
	docker push $(IMAGE_REPOSITORY)/educates-base-environment:$(PACKAGE_VERSION)

build-jdk8-environment: build-base-environment
	docker build --platform $(DOCKER_PLATFORM) --build-arg PACKAGE_VERSION=$(PACKAGE_VERSION) -t $(IMAGE_REPOSITORY)/educates-jdk8-environment:$(PACKAGE_VERSION) workshop-images/jdk8-environment

push-jdk8-environment: build-jdk8-environment
	docker push $(IMAGE_REPOSITORY)/educates-jdk8-environment:$(PACKAGE_VERSION)

build-jdk11-environment: build-base-environment
	docker build --platform $(DOCKER_PLATFORM) --build-arg PACKAGE_VERSION=$(PACKAGE_VERSION) -t $(IMAGE_REPOSITORY)/educates-jdk11-environment:$(PACKAGE_VERSION) workshop-images/jdk11-environment

push-jdk11-environment: build-jdk11-environment
	docker push $(IMAGE_REPOSITORY)/educates-jdk11-environment:$(PACKAGE_VERSION)

build-jdk17-environment: build-base-environment
	docker build --platform $(DOCKER_PLATFORM) --build-arg PACKAGE_VERSION=$(PACKAGE_VERSION) -t $(IMAGE_REPOSITORY)/educates-jdk17-environment:$(PACKAGE_VERSION) workshop-images/jdk17-environment

push-jdk17-environment: build-jdk17-environment
	docker push $(IMAGE_REPOSITORY)/educates-jdk17-environment:$(PACKAGE_VERSION)

build-conda-environment: build-base-environment
	docker build --platform $(DOCKER_PLATFORM) --build-arg PACKAGE_VERSION=$(PACKAGE_VERSION) -t $(IMAGE_REPOSITORY)/educates-conda-environment:$(PACKAGE_VERSION) workshop-images/conda-environment

push-conda-environment: build-conda-environment
	docker push $(IMAGE_REPOSITORY)/educates-conda-environment:$(PACKAGE_VERSION)

build-docker-registry:
	docker build --platform $(DOCKER_PLATFORM) -t $(IMAGE_REPOSITORY)/educates-docker-registry:$(PACKAGE_VERSION) docker-registry

push-docker-registry: build-docker-registry
	docker push $(IMAGE_REPOSITORY)/educates-docker-registry:$(PACKAGE_VERSION)

build-pause-container:
	docker build --platform $(DOCKER_PLATFORM) -t $(IMAGE_REPOSITORY)/educates-pause-container:$(PACKAGE_VERSION) pause-container

push-pause-container: build-pause-container
	docker push $(IMAGE_REPOSITORY)/educates-pause-container:$(PACKAGE_VERSION)

build-secrets-manager:
	docker build --platform $(DOCKER_PLATFORM) -t $(IMAGE_REPOSITORY)/educates-secrets-manager:$(PACKAGE_VERSION) secrets-manager

push-secrets-manager: build-secrets-manager
	docker push $(IMAGE_REPOSITORY)/educates-secrets-manager:$(PACKAGE_VERSION)

verify-cluster-essentials-config:
ifneq ("$(wildcard testing/educates-cluster-essentials-values.yaml)","")
	@ytt --file carvel-packages/cluster-essentials/bundle/config --data-values-file testing/educates-cluster-essentials-values.yaml
else
	@ytt --file carvel-packages/cluster-essentials/bundle/config
endif

push-cluster-essentials-bundle:
	ytt -f carvel-packages/cluster-essentials/bundle/config | kbld -f - --imgpkg-lock-output carvel-packages/cluster-essentials/bundle/.imgpkg/images.yml
	imgpkg push -b $(IMAGE_REPOSITORY)/educates-cluster-essentials:$(RELEASE_VERSION) -f carvel-packages/cluster-essentials/bundle
	mkdir -p testing
	ytt -f carvel-packages/cluster-essentials/bundle --data-values-schema-inspect -o openapi-v3 > testing/educates-cluster-essentials-schema-openapi.yaml
	ytt -f carvel-packages/cluster-essentials/config/package.yaml -f carvel-packages/cluster-essentials/config/schema.yaml -v imageRegistry.host=$(IMAGE_REPOSITORY) -v version=$(RELEASE_VERSION) -v releasedAt=`date -u +"%Y-%m-%dT%H:%M:%SZ"` --data-value-file openapi=testing/educates-cluster-essentials-schema-openapi.yaml > testing/educates-cluster-essentials.yaml

deploy-cluster-essentials:
ifneq ("$(wildcard testing/educates-cluster-essentials-values.yaml)","")
	ytt --file carvel-packages/cluster-essentials/bundle/config --data-values-file testing/educates-cluster-essentials-values.yaml | kapp deploy -a educates-cluster-essentials -f - -y
else
	ytt --file carvel-packages/cluster-essentials/bundle/config | kapp deploy -a educates-cluster-essentials -f - -y
endif

delete-cluster-essentials:
	kapp delete -a educates-cluster-essentials -y

deploy-cluster-essentials-bundle:
	kubectl get ns/educates-package || kubectl create ns educates-package
	kubectl apply --namespace educates-package -f package-repository/packages/cluster-essentials.educates.dev/metadata.yaml
	kubectl apply --namespace educates-package -f testing/educates-cluster-essentials.yaml
ifneq ("$(wildcard testing/educates-cluster-essentials-values.yaml)","")
	kctrl package install --namespace educates-package --package-install educates-cluster-essentials --package cluster-essentials.educates.dev --version $(RELEASE_VERSION) --values-file testing/educates-cluster-essentials-values.yaml
else
	kctrl package install --namespace educates-package --package-install educates-cluster-essentials --package cluster-essentials.educates.dev --version $(RELEASE_VERSION)
endif

delete-cluster-essentials-bundle:
	kctrl package installed delete --namespace educates-package --package-install educates-cluster-essentials -y

verify-training-platform-config:
ifneq ("$(wildcard testing/educates-training-platform-values.yaml)","")
	@ytt --file carvel-packages/training-platform/bundle/config --data-values-file testing/educates-training-platform-values.yaml
else
	@ytt --file carvel-packages/training-platform/bundle/config
endif

push-training-platform-bundle:
	ytt -f carvel-packages/training-platform/config/images.yaml -f carvel-packages/training-platform/config/schema.yaml -v imageRegistry.host=$(IMAGE_REPOSITORY) -v version=$(PACKAGE_VERSION) > carvel-packages/training-platform/bundle/kbld-images.yaml
	cat carvel-packages/training-platform/bundle/kbld-images.yaml | kbld -f - --imgpkg-lock-output carvel-packages/training-platform/bundle/.imgpkg/images.yml
	imgpkg push -b $(IMAGE_REPOSITORY)/educates-training-platform:$(RELEASE_VERSION) -f carvel-packages/training-platform/bundle
	mkdir -p testing
	ytt -f carvel-packages/training-platform/bundle --data-values-schema-inspect -o openapi-v3 > testing/educates-training-platform-schema-openapi.yaml
	ytt -f carvel-packages/training-platform/config/package.yaml -f carvel-packages/training-platform/config/schema.yaml -v imageRegistry.host=$(IMAGE_REPOSITORY) -v version=$(RELEASE_VERSION) -v releasedAt=`date -u +"%Y-%m-%dT%H:%M:%SZ"` --data-value-file openapi=testing/educates-training-platform-schema-openapi.yaml > testing/educates-training-platform.yaml

deploy-training-platform:
ifneq ("$(wildcard testing/educates-training-platform-values.yaml)","")
	ytt --file carvel-packages/training-platform/bundle/config --data-values-file testing/educates-training-platform-values.yaml | kapp deploy -a educates-training-platform -f - -y
else
	ytt --file carvel-packages/training-platform/bundle/config | kapp deploy -a educates-training-platform -f - -y
endif

restart-training-platform:
	kubectl rollout restart deployment/secrets-manager -n educates
	kubectl rollout restart deployment/session-manager -n educates

delete-training-platform: delete-workshop
	kapp delete -a educates-training-platform -y

deploy-training-platform-bundle:
	kubectl get ns/educates-package || kubectl create ns educates-package
	kubectl apply --namespace educates-package -f package-repository/packages/training-platform.educates.dev/metadata.yaml
	kubectl apply --namespace educates-package -f testing/educates-training-platform.yaml
ifneq ("$(wildcard testing/educates-training-platform-values.yaml)","")
	kctrl package install --namespace educates-package --package-install educates-training-platform --package training-platform.educates.dev --version $(RELEASE_VERSION) --values-file testing/educates-training-platform-values.yaml
else
	kctrl package install --namespace educates-package --package-install educates-training-platform --package training-platform.educates.dev --version $(RELEASE_VERSION)
endif

delete-training-platform-bundle:
	kctrl package installed delete --namespace educates-package --package-install educates-training-platform -y

client-programs-educates:
	(cd client-programs; go build -o educates cmd/educates/main.go)

client-programs: client-programs-educates

deploy-workshop:
	kubectl apply -f https://github.com/vmware-tanzu-labs/lab-k8s-fundamentals/releases/download/5.0/workshop.yaml
	kubectl apply -f https://github.com/vmware-tanzu-labs/lab-k8s-fundamentals/releases/download/5.0/trainingportal.yaml
	STATUS=1; ATTEMPTS=0; ROLLOUT_STATUS_CMD="kubectl rollout status deployment/training-portal -n lab-k8s-fundamentals-ui"; until [ $$STATUS -eq 0 ] || $$ROLLOUT_STATUS_CMD || [ $$ATTEMPTS -eq 5 ]; do sleep 5; $$ROLLOUT_STATUS_CMD; STATUS=$$?; ATTEMPTS=$$((ATTEMPTS + 1)); done

delete-workshop:
	-kubectl delete trainingportal,workshop lab-k8s-fundamentals --cascade=foreground

open-workshop:
	URL=`kubectl get trainingportal/lab-k8s-fundamentals -o go-template={{.status.educates.url}}`; (test -x /usr/bin/xdg-open && xdg-open $$URL) || (test -x /usr/bin/open && open $$URL) || true

prune-images:
	docker image prune --force

prune-docker:
	docker system prune --force

prune-builds:
	rm -rf workshop-images/base-environment/opt/gateway/build
	rm -rf workshop-images/base-environment/opt/gateway/node_modules
	rm -rf workshop-images/base-environment/opt/helper/node_modules
	rm -rf workshop-images/base-environment/opt/helper/out
	rm -rf workshop-images/base-environment/opt/renderer/build
	rm -rf workshop-images/base-environment/opt/renderer/node_modules
	rm -rf training-portal/venv
	rm -f client-programs/educates

prune-registry:
	docker exec educates-registry registry garbage-collect /etc/docker/registry/config.yml --delete-untagged=true

prune-all: prune-docker prune-builds prune-registry
