#!/bin/bash

set -x

set -eo pipefail

rm -rf build

tsc

browserify build/frontend/scripts/eduk8s.js --standalone eduk8s -o build/frontend/scripts/eduk8s-bundle.js
cat build/frontend/scripts/eduk8s-bundle.js | uglifyjs > build/frontend/scripts/eduk8s-bundle.min.js

browserify build/frontend/scripts/testing/dashboard.js --standalone dashboard -o build/frontend/scripts/testing/dashboard-bundle.js
cat build/frontend/scripts/testing/dashboard-bundle.js | uglifyjs > build/frontend/scripts/testing/dashboard-bundle.min.js