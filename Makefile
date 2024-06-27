IMAGE_REPOSITORY = localhost:5001
PACKAGE_VERSION = latest
RELEASE_VERSION = 0.0.1

UNAME_SYSTEM := $(shell uname -s | tr '[:upper:]' '[:lower:]')
UNAME_MACHINE := $(shell uname -m)

DOCKER_PLATFORM = linux/amd64

TARGET_SYSTEM = $(UNAME_SYSTEM)
TARGET_MACHINE = $(UNAME_MACHINE)

ifeq ($(UNAME_MACHINE),x86_64)
TARGET_MACHINE = amd64
endif

TARGET_PLATFORM = $(TARGET_SYSTEM)-$(TARGET_MACHINE)
DOCKER_PLATFORM = linux/$(TARGET_MACHINE)

all: push-all-images # deploy-installer deploy-workshop

build-all-images: build-session-manager build-training-portal \
  build-base-environment build-jdk8-environment build-jdk11-environment \
  build-jdk17-environment build-jdk21-environment \
  build-conda-environment build-docker-registry \
  build-pause-container build-secrets-manager build-tunnel-manager \
  build-image-cache build-assets-server

push-all-images: push-session-manager push-training-portal \
  push-base-environment push-jdk8-environment push-jdk11-environment \
  push-jdk17-environment push-jdk21-environment \
  push-conda-environment push-docker-registry \
  push-pause-container push-secrets-manager push-tunnel-manager \
  push-image-cache push-assets-server

build-core-images: build-session-manager build-training-portal \
  build-base-environment build-docker-registry build-pause-container \
  build-secrets-manager build-tunnel-manager build-image-cache \
  build-assets-server

push-core-images: push-session-manager push-training-portal \
  push-base-environment push-docker-registry push-pause-container \
  push-secrets-manager push-tunnel-manager push-image-cache \
  push-assets-server

build-session-manager:
	docker build --progress plain --platform $(DOCKER_PLATFORM) -t $(IMAGE_REPOSITORY)/educates-session-manager:$(PACKAGE_VERSION) session-manager

push-session-manager: build-session-manager
	docker push $(IMAGE_REPOSITORY)/educates-session-manager:$(PACKAGE_VERSION)

build-training-portal:
	docker build --progress plain --platform $(DOCKER_PLATFORM) -t $(IMAGE_REPOSITORY)/educates-training-portal:$(PACKAGE_VERSION) training-portal

push-training-portal: build-training-portal
	docker push $(IMAGE_REPOSITORY)/educates-training-portal:$(PACKAGE_VERSION)

build-base-environment:
	docker build --progress plain --platform $(DOCKER_PLATFORM) -t $(IMAGE_REPOSITORY)/educates-base-environment:$(PACKAGE_VERSION) workshop-images/base-environment

push-base-environment: build-base-environment
	docker push $(IMAGE_REPOSITORY)/educates-base-environment:$(PACKAGE_VERSION)

build-jdk8-environment: build-base-environment
	docker build --progress plain --platform $(DOCKER_PLATFORM) --build-arg PACKAGE_VERSION=$(PACKAGE_VERSION) -t $(IMAGE_REPOSITORY)/educates-jdk8-environment:$(PACKAGE_VERSION) workshop-images/jdk8-environment

push-jdk8-environment: build-jdk8-environment
	docker push $(IMAGE_REPOSITORY)/educates-jdk8-environment:$(PACKAGE_VERSION)

build-jdk11-environment: build-base-environment
	docker build --progress plain --platform $(DOCKER_PLATFORM) --build-arg PACKAGE_VERSION=$(PACKAGE_VERSION) -t $(IMAGE_REPOSITORY)/educates-jdk11-environment:$(PACKAGE_VERSION) workshop-images/jdk11-environment

push-jdk11-environment: build-jdk11-environment
	docker push $(IMAGE_REPOSITORY)/educates-jdk11-environment:$(PACKAGE_VERSION)

build-jdk17-environment: build-base-environment
	docker build --progress plain --platform $(DOCKER_PLATFORM) --build-arg PACKAGE_VERSION=$(PACKAGE_VERSION) -t $(IMAGE_REPOSITORY)/educates-jdk17-environment:$(PACKAGE_VERSION) workshop-images/jdk17-environment

push-jdk17-environment: build-jdk17-environment
	docker push $(IMAGE_REPOSITORY)/educates-jdk17-environment:$(PACKAGE_VERSION)

build-jdk21-environment: build-base-environment
	docker build --progress plain --platform $(DOCKER_PLATFORM) --build-arg PACKAGE_VERSION=$(PACKAGE_VERSION) -t $(IMAGE_REPOSITORY)/educates-jdk21-environment:$(PACKAGE_VERSION) workshop-images/jdk21-environment

push-jdk21-environment: build-jdk21-environment
	docker push $(IMAGE_REPOSITORY)/educates-jdk21-environment:$(PACKAGE_VERSION)

build-conda-environment: build-base-environment
	docker build --progress plain --platform $(DOCKER_PLATFORM) --build-arg PACKAGE_VERSION=$(PACKAGE_VERSION) -t $(IMAGE_REPOSITORY)/educates-conda-environment:$(PACKAGE_VERSION) workshop-images/conda-environment

push-conda-environment: build-conda-environment
	docker push $(IMAGE_REPOSITORY)/educates-conda-environment:$(PACKAGE_VERSION)

build-desktop-environment: build-base-environment
	docker build --progress plain --platform $(DOCKER_PLATFORM) --build-arg PACKAGE_VERSION=$(PACKAGE_VERSION) -t $(IMAGE_REPOSITORY)/educates-desktop-environment:$(PACKAGE_VERSION) workshop-images/desktop-environment

push-desktop-environment: build-desktop-environment
	docker push $(IMAGE_REPOSITORY)/educates-desktop-environment:$(PACKAGE_VERSION)

build-docker-registry:
	docker build --progress plain --platform $(DOCKER_PLATFORM) -t $(IMAGE_REPOSITORY)/educates-docker-registry:$(PACKAGE_VERSION) docker-registry

push-docker-registry: build-docker-registry
	docker push $(IMAGE_REPOSITORY)/educates-docker-registry:$(PACKAGE_VERSION)

build-pause-container:
	docker build --progress plain --platform $(DOCKER_PLATFORM) -t $(IMAGE_REPOSITORY)/educates-pause-container:$(PACKAGE_VERSION) pause-container

push-pause-container: build-pause-container
	docker push $(IMAGE_REPOSITORY)/educates-pause-container:$(PACKAGE_VERSION)

build-secrets-manager:
	docker build --progress plain --platform $(DOCKER_PLATFORM) -t $(IMAGE_REPOSITORY)/educates-secrets-manager:$(PACKAGE_VERSION) secrets-manager

push-secrets-manager: build-secrets-manager
	docker push $(IMAGE_REPOSITORY)/educates-secrets-manager:$(PACKAGE_VERSION)

build-tunnel-manager:
	docker build --progress plain --platform $(DOCKER_PLATFORM) -t $(IMAGE_REPOSITORY)/educates-tunnel-manager:$(PACKAGE_VERSION) tunnel-manager

push-tunnel-manager: build-tunnel-manager
	docker push $(IMAGE_REPOSITORY)/educates-tunnel-manager:$(PACKAGE_VERSION)

build-image-cache:
	docker build --progress plain --platform $(DOCKER_PLATFORM) -t $(IMAGE_REPOSITORY)/educates-image-cache:$(PACKAGE_VERSION) image-cache

push-image-cache: build-image-cache
	docker push $(IMAGE_REPOSITORY)/educates-image-cache:$(PACKAGE_VERSION)

build-assets-server:
	docker build --progress plain --platform $(DOCKER_PLATFORM) -t $(IMAGE_REPOSITORY)/educates-assets-server:$(PACKAGE_VERSION) assets-server

push-assets-server: build-assets-server
	docker push $(IMAGE_REPOSITORY)/educates-assets-server:$(PACKAGE_VERSION)

verify-installer-config:
ifneq ("$(wildcard developer-testing/educates-installer-values.yaml)","")
	@ytt --file carvel-packages/installer/bundle/config --data-values-file developer-testing/educates-installer-values.yaml
else
	@echo "No values file found. Please create developer-testing/educates-installer-values.yaml"
	exit 1
endif

push-installer-bundle:
	ytt -f carvel-packages/installer/config/images.yaml -f carvel-packages/installer/config/schema.yaml -v imageRegistry.host=$(IMAGE_REPOSITORY) -v version=$(PACKAGE_VERSION) > carvel-packages/installer/bundle/kbld/kbld-images.yaml
   # For local development, we just need to lock educates images. Everything else can be referenced by tag from real origin.
	cat carvel-packages/installer/bundle/kbld/kbld-images.yaml | kbld -f - --imgpkg-lock-output carvel-packages/installer/bundle/.imgpkg/images.yml
	imgpkg push -b $(IMAGE_REPOSITORY)/educates-installer:$(RELEASE_VERSION) -f carvel-packages/installer/bundle
	mkdir -p developer-testing
	ytt -f carvel-packages/installer/config/app.yaml -f carvel-packages/installer/config/schema.yaml -v imageRegistry.host=$(IMAGE_REPOSITORY) -v version=$(RELEASE_VERSION) > developer-testing/educates-installer-app.yaml

deploy-platform:
ifneq ("$(wildcard developer-testing/educates-installer-values.yaml)","")
	-kubectl create ns educates-installer
	ytt --file carvel-packages/installer/bundle/config --data-values-file developer-testing/educates-installer-values.yaml | kapp deploy -a label:installer=educates-installer.app -n educates-installer -f - -y
else
	@echo "No values file found. Please create developer-testing/educates-installer-values.yaml"
	exit 1
endif

delete-platform:
	kapp delete -a label:installer=educates-installer.app -y
	-kubectl delete ns educates-installer

deploy-platform-app: push-installer-bundle
ifeq ("$(wildcard developer-testing/educates-installer-values.yaml)","")
	@echo "No values file found. Please create developer-testing/educates-installer-values.yaml"
	exit 1
endif
	-kubectl apply --namespace educates-installer -f carvel-packages/installer/config/rbac.yaml
	kubectl create secret generic educates-installer --from-file=developer-testing/educates-installer-values.yaml -o yaml --dry-run=client | kubectl apply -n educates-installer -f -
	kubectl apply --namespace educates-installer -f developer-testing/educates-installer-app.yaml

delete-platform-app:
	kubectl delete --namespace educates-installer -f developer-testing/educates-installer-app.yaml
	-kubectl delete secret educates-installer -n educates-installer
	-kubectl delete --namespace educates-installer -f carvel-packages/installer/config/rbac.yaml

restart-training-platform:
	kubectl rollout restart deployment/secrets-manager -n educates
	kubectl rollout restart deployment/session-manager -n educates

client-programs-educates:
	rm -rf client-programs/pkg/renderer/files
	mkdir client-programs/pkg/renderer/files
	mkdir -p client-programs/bin
	cp -rp workshop-images/base-environment/opt/eduk8s/etc/themes client-programs/pkg/renderer/files/
	(cd client-programs; go build -gcflags=all="-N -l" -o bin/educates-$(TARGET_PLATFORM) cmd/educates/main.go)

build-client-programs: client-programs-educates

push-client-programs : build-client-programs
ifeq ($(UNAME_SYSTEM),darwin)
	(cd client-programs; GOOS=linux GOARCH=amd64 go build -o bin/educates-linux-amd64 cmd/educates/main.go)
	(cd client-programs; GOOS=linux GOARCH=arm64 go build -o bin/educates-linux-arm64 cmd/educates/main.go)
endif
ifeq ($(UNAME_SYSTEM),linux)
ifeq ($(TARGET_PLATFORM),arm64)
	(cd client-programs; GOOS=linux GOARCH=amd64 go build -o bin/educates-linux-amd64 cmd/educates/main.go)
endif
ifeq ($(TARGET_PLATFORM),amd64)
	(cd client-programs; GOOS=linux GOARCH=arm64 go build -o bin/educates-linux-arm64 cmd/educates/main.go)
endif
endif
	imgpkg push -i $(IMAGE_REPOSITORY)/educates-client-programs:$(PACKAGE_VERSION) -f client-programs/bin

build-docker-extension : push-client-programs
	$(MAKE) -C docker-extension build-extension REPOSITORY=$(IMAGE_REPOSITORY) TAG=$(PACKAGE_VERSION)

install-docker-extension : build-docker-extension
	$(MAKE) -C docker-extension install-extension REPOSITORY=$(IMAGE_REPOSITORY) TAG=$(PACKAGE_VERSION)

update-docker-extension : build-docker-extension
	$(MAKE) -C docker-extension update-extension REPOSITORY=$(IMAGE_REPOSITORY) TAG=$(PACKAGE_VERSION)

project-docs/venv :
	python3 -m venv project-docs/venv
	project-docs/venv/bin/pip install -r project-docs/requirements.txt
 
build-project-docs : project-docs/venv
	source project-docs/venv/bin/activate && make -C project-docs html

open-project-docs :
	open project-docs/_build/html/index.html || \
        xdg-open project-docs/_build/html/index.html

clean-project-docs:
	rm -rf project-docs/venv
	rm -rf project-docs/_build

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
	rm -rf client-programs/bin
	rm -rf client-programs/pkg/renderer/files
	rm -rf project-docs/venv
	rm -rf project-docs/_build

prune-registry:
	docker exec educates-registry registry garbage-collect /etc/docker/registry/config.yml --delete-untagged=true

prune-all: prune-docker prune-builds prune-registry
