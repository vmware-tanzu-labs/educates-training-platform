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
  for test_dir in `ls -d {kind,eks,custom,gke}/test*/`
  do
    pushd ${DIR}/${test_dir} >/dev/null 2>&1
    echo "---------------------------------------------"
    echo "Scenario ${test_dir}:"
    echo "==="
    cat description.md
    echo "==="
    echo ""
    popd >/dev/null 2>&1
  done
  popd >/dev/null 2>&1
}

function todo {
  pushd ${DIR} >/dev/null 2>&1
  for test_dir in `ls -d {kind,eks,custom,gke}/test*/`
  do
    pushd ${DIR}/${test_dir} >/dev/null 2>&1
    cat description.md | grep TODO >/dev/null 2>&1
    result=$?
    if [[ "$result" -eq 0 ]]
    then
      echo "---------------------------------------------"
      echo "Scenario ${test_dir}:"
      echo "==="
      cat description.md
      echo "==="
      echo ""
    fi
    popd >/dev/null 2>&1
  done
  popd >/dev/null 2>&1
}

function test {
  pushd ${DIR} >/dev/null 2>&1
  for test_dir in `ls -d {kind,eks,custom,gke}/test*/`
  do
    pushd ${DIR}/${test_dir} >/dev/null 2>&1
    echo "---------------------------------------------"
    echo "Scenario ${test_dir}:"
    echo "==="
    cat description.md
    echo "==="
    RESULT_VALUES=$(ytt --data-value-yaml debug=false --data-values-file values.yaml -f ${DIR}/../bundle/config/ytt --data-value-yaml debug=true | yq)
    diff <(echo "$RESULT_VALUES") <(cat expected.yaml | yq)
    result=$?
    [[ "$result" -eq 0 ]] && echo "Result Diff Values/Expected: OK" || echo -e "Result Diff Values/Expected: ${RED}NO OK${NC}"
    ytt --data-value-yaml debug=false --data-values-file values.yaml -f ${DIR}/../bundle/config/ytt --data-value-yaml debug=true >/dev/null 2>&1
    result=$?
    [[ "$result" -eq 0 ]] && echo "Result ytt processing: OK" || echo -e "Result ytt processing: ${RED}NO OK${NC}"
    popd >/dev/null 2>&1  
  done
  popd >/dev/null 2>&1 
}

function debug {
  pushd ${DIR} >/dev/null 2>&1
  for test_dir in `ls -d {kind,eks,custom,gke}/test*/`
  do
    pushd ${DIR}/${test_dir} >/dev/null 2>&1
    echo "---------------------------------------------"
    echo "Scenario ${test_dir}:"
    echo "==="
    cat description.md
    echo "==="
    ytt --data-value-yaml debug=false --data-values-file values.yaml -f ${DIR}/../bundle/config/ytt --data-value-yaml debug=true | yq
    result=$?
    [[ "$result" -eq 0 ]] && echo "Result: OK" || echo -e "Result: ${RED}NO OK${NC}"
    popd >/dev/null 2>&1  
  done
  popd >/dev/null 2>&1 
}


[ "$1" == "-h" ] || [ "$1" == "--help" ] && help && exit 0
[ "$1" == "-d" ] || [ "$1" == "--debug" ] && debug && exit 0
[ "$1" == "-t" ] || [ "$1" == "--todo" ] && todo && exit 0
test

