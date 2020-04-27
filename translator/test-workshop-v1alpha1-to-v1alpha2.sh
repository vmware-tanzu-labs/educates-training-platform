#!/bin/sh

HERE=`dirname $0`

curl -s --header "Content-Type: application/json" \
  --data "`cat $HERE/test-workshop-v1alpha1-to-v1alpha2.json`" \
  http://localhost:8080/api/translate | jq
