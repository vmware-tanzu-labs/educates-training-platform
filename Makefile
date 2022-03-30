IMAGE_REPOSITORY = localhost:5001
PACKAGE_VERSION = latest

all:

build-all-images: build-session-manager build-training-portal \
  build-base-environment build-jdk8-environment build-jdk11-environment \
  build-conda-environment build-docker-in-docker

push-all-images: push-session-manager push-training-portal \
  push-base-environment push-jdk8-environment push-jdk11-environment \
  push-conda-environment push-docker-in-docker

build-session-manager:
	docker build -t $(IMAGE_REPOSITORY)/session-manager:$(PACKAGE_VERSION) session-manager

push-session-manager: build-session-manager
	docker push $(IMAGE_REPOSITORY)/session-manager:$(PACKAGE_VERSION)

build-training-portal:
	docker build -t $(IMAGE_REPOSITORY)/training-portal:$(PACKAGE_VERSION) training-portal

push-training-portal: build-training-portal
	docker push $(IMAGE_REPOSITORY)/training-portal:$(PACKAGE_VERSION)

build-base-environment:
	docker build -t $(IMAGE_REPOSITORY)/base-environment:$(PACKAGE_VERSION) workshop-images/base-environment

push-base-environment: build-base-environment
	docker push $(IMAGE_REPOSITORY)/base-environment:$(PACKAGE_VERSION)

build-jdk8-environment:
	docker build --build-arg PACKAGE_VERSION=$(PACKAGE_VERSION) -t $(IMAGE_REPOSITORY)/jdk8-environment:$(PACKAGE_VERSION) workshop-images/jdk8-environment

push-jdk8-environment: build-jdk8-environment
	docker push $(IMAGE_REPOSITORY)/jdk8-environment:$(PACKAGE_VERSION)

build-jdk11-environment:
	docker build --build-arg PACKAGE_VERSION=$(PACKAGE_VERSION) -t $(IMAGE_REPOSITORY)/jdk11-environment:$(PACKAGE_VERSION) workshop-images/jdk11-environment

push-jdk11-environment: build-jdk11-environment
	docker push $(IMAGE_REPOSITORY)/jdk11-environment:$(PACKAGE_VERSION)

build-conda-environment:
	docker build --build-arg PACKAGE_VERSION=$(PACKAGE_VERSION) -t $(IMAGE_REPOSITORY)/conda-environment:$(PACKAGE_VERSION) workshop-images/conda-environment

push-conda-environment: build-conda-environment
	docker push $(IMAGE_REPOSITORY)/conda-environment:$(PACKAGE_VERSION)

build-docker-in-docker:
	docker build -t $(IMAGE_REPOSITORY)/docker-in-docker:$(PACKAGE_VERSION) docker-in-docker

push-docker-in-docker: build-docker-in-docker
	docker push $(IMAGE_REPOSITORY)/docker-in-docker:$(PACKAGE_VERSION)

deploy-educates:
ifneq ("$(wildcard values.yaml)","")
	ytt --file bundle/config --data-values-file values.yaml | kapp deploy -a educates-training-platform -f - -y
else
	ytt --file bundle/config | kapp deploy -a educates-training-platform -f - -y
endif

delete-educates: delete-workshop
	kapp delete -a educates-training-platform -y

deploy-workshop:
	kubectl apply -f https://github.com/vmware-tanzu-labs/lab-k8s-fundamentals/releases/download/1.0/workshop.yaml
	kubectl apply -f https://github.com/vmware-tanzu-labs/lab-k8s-fundamentals/releases/download/1.0/training-portal.yaml

delete-workshop:
	-kubectl delete trainingportal,workshop lab-k8s-fundamentals --cascade=foreground

open-workshop:
	URL=`kubectl get trainingportal/lab-k8s-fundamentals -o go-template={{.status.eduk8s.url}}`; (test -x /usr/bin/xdg-open && xdg-open $$URL) || (test -x /usr/bin/open && open $$URL) || true

prune-images:
	docker image prune --force

prune-docker:
	docker system prune --force
