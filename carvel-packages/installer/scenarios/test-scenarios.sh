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
  local pattern=$1
  pushd ${DIR} >/dev/null 2>&1
  for test_dir in `ls -d {kind,eks,custom,gke,vcluster,generic}/test*/`
  do
    if [[ $test_dir != *${pattern}* ]]; then
      continue
    fi
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
  local pattern=$1
  echo $pattern
  pushd ${DIR} >/dev/null 2>&1
  for test_dir in `ls -d {kind,eks,custom,gke,vcluster,generic}/test*/`
  do
    if [[ $test_dir != *${pattern}* ]]; then
      continue
    fi
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
  local pattern=$1

  pushd ${DIR} >/dev/null 2>&1
  for test_dir in `ls -d {kind,eks,custom,gke,vcluster,generic}/test*/`
  do
    if [[ $test_dir != *${pattern}* ]]; then
      continue
    fi
    pushd ${DIR}/${test_dir} >/dev/null 2>&1
    echo "---------------------------------------------"
    echo "Scenario ${test_dir}:"
    echo "==="
    cat description.md
    echo "==="
    RESULT_VALUES=$(ytt --data-values-file values.yaml -f ${DIR}/../bundle/config/ytt --data-value-yaml debug=true | yq)
    diff <(echo "$RESULT_VALUES") <(cat expected.yaml | yq)
    result=$?
    [[ "$result" -eq 0 ]] && echo "Result Diff Values/Expected: OK" || echo -e "Result Diff Values/Expected: ${RED}NO OK${NC}"
    ytt --data-values-file values.yaml -f ${DIR}/../bundle/config/ytt --data-value-yaml debug=false >/dev/null 2>&1
    result=$?
    [[ "$result" -eq 0 ]] && echo "Result ytt processing: OK" || echo -e "Result ytt processing: ${RED}NO OK${NC}"
    popd >/dev/null 2>&1  
  done
  popd >/dev/null 2>&1 
}

function debug {
  local pattern=$1
  pushd ${DIR} >/dev/null 2>&1
  for test_dir in `ls -d {kind,eks,custom,gke,vcluster,generic}/test*/`
  do
    if [[ $test_dir != *${pattern}* ]]; then
      continue
    fi
    pushd ${DIR}/${test_dir} >/dev/null 2>&1
    echo "---------------------------------------------"
    echo "Scenario ${test_dir}:"
    echo "==="
    cat description.md
    echo "==="
    RESULT_VALUES=$(ytt --data-values-file values.yaml -f ${DIR}/../bundle/config/ytt --data-value-yaml debug=true)
    result=$?
    echo "$RESULT_VALUES" | yq
    [[ "$result" -eq 0 ]] ||
      echo -e "${RED}Error processing ytt template${NC}"
    popd >/dev/null 2>&1  
  done
  popd >/dev/null 2>&1 
}

for arg in "$@"
do
  case $arg in
    -h|--help)
      shift
      help ${1:-"*"}
      exit 0
      ;;
    -d|--debug)
      shift
      debug ${1:-"*"}
      exit 0
      ;;
    -t|--todo)
      shift
      todo ${1:-"*"}
      exit 0
      ;;
    *)
      test ${1:-"*"}
      exit 0
      ;;
  esac
done
# this last one is because it's not doing the for loop when there's no arguments
test "*"

