#!/bin/bash

# Handle source locations that might be a symlink (ref: http://bit.ly/2kcvSCS)
SOURCE="${BASH_SOURCE[0]}"
while [ -h "$SOURCE" ]; do # resolve $SOURCE until the file is no longer a symlink
  DIR="$( cd -P "$( dirname "$SOURCE" )" && pwd )"
  SOURCE="$(readlink "$SOURCE")"
  [[ $SOURCE != /* ]] && SOURCE="$DIR/$SOURCE" # if $SOURCE was a relative symlink, we need to resolve it relative to the path where the symlink file was located
done
DIR="$( cd -P "$( dirname "$SOURCE" )" && pwd )"

#
# Colors for echo
# 
RED='\033[0;31m'
NC='\033[0m' # No Color


pushd ${DIR} >/dev/null 2>&1
for test in `ls test*.yaml`
do
  ytt --data-value-yaml debug=false --data-values-file $test -f ../src/bundle/config/ytt >/dev/null 2>&1
  result=$?
  [[ "$result" -eq 0 ]] && echo "OK: $test" || echo -e "${RED}NO OK: $test${NC}"

done
popd >/dev/null 2>&1