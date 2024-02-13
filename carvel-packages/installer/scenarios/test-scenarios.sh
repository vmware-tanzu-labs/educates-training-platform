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

function help {
pushd ${DIR} >/dev/null 2>&1
for test in `ls test*.yaml`
do
  echo "---------------------------------------------"
  echo "Scenario:"
  echo " - File: $test"
  head -n 1 $test | sed 's/#! / - Description: /'
  echo ""
done
popd >/dev/null 2>&1
}

[ "$1" == "-h" ] || [ "$1" == "--help" ] && help && exit 0

pushd ${DIR} >/dev/null 2>&1
for test in `ls test*.yaml`
do
  echo "---------------------------------------------"
  echo "Scenario:"
  echo " - File: $test"
  head -n 1 $test | sed 's/#! / - Description: /'
  ytt --data-value-yaml debug=false --data-values-file $test -f ../bundle/config/ytt >/dev/null 2>&1
  result=$?
  [[ "$result" -eq 0 ]] && echo "Result: OK" || echo -e "Result: ${RED}NO OK${NC}"

done
popd >/dev/null 2>&1