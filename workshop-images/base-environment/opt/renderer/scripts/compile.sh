#!/bin/bash

set -x

set -eo pipefail

rm -rf build

tsc

browserify build/frontend/scripts/educates.js --standalone educates -o build/frontend/scripts/educates-bundle.js
cat build/frontend/scripts/educates-bundle.js | uglifyjs > build/frontend/scripts/educates-bundle.min.js
