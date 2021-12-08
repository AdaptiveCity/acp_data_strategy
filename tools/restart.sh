#!/bin/bash

if [ -z "$1" ]
then
    echo 'Usage "tools/restart.sh <partial command name>"'
    echo 'e.g.: "tools/restart.sh api_bim"'
    exit 0
fi

pids=( $(pgrep -f ${1}) )
for pid in "${pids[@]}"
do
  if [[ ${pid} != $$ ]]
  then
    echo Killing process ${pid}, $(ps -o cmd= fp ${pid})
    kill ${pid} 2>/dev/null
    while kill -0 ${pid} 2>/dev/null
    do
        sleep 1
    done
    echo Process ${pid} killed
  fi
done

echo
echo "Issuing run.sh command for all API processes:"
./run.sh

sleep 2

echo
echo "Showing status.sh for all API processes:"
tools/status.sh

