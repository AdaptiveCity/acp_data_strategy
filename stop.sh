#!/bin/bash

# Kill running acp_space_render processes

for name in api_bim api_sensors api_readings api_space
do
    pid=$(pgrep -f ${name})
    if [ $? -eq 0 ]
    then
        echo $(date '+%s.%3N') "stopping ${name}"
        pkill -9 -f ${name}
    else
        echo $(date '+%s.%3N') "${name} not running"
    fi
done



