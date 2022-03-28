REGISTRY = localhost:5001

all:

build-all-images: build-session-manager build-training-portal

push-all-images: push-session-manager push-training-portal

build-session-manager:
	docker build -t $(REGISTRY)/session-manager:latest session-manager

push-session-manager: build-session-manager
	docker push $(REGISTRY)/session-manager:latest

build-training-portal:
	docker build -t $(REGISTRY)/training-portal:latest training-portal

push-training-portal: build-training-portal
	docker push $(REGISTRY)/training-portal:latest

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