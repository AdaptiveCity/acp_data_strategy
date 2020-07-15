#!/bin/bash

# A simple test script to see if ACP data api processes are running

exit_code=0

for name in api_bim api_sensors api_readings api_space
do
    pid=$(pgrep -f "python3 ${name}.py")
    if [ $? -eq 0 ]
    then
        echo $(date '+%s.%3N') "${name}.py      OK running as PID $pid"
    else
        echo $(date '+%s.%3N') "${name}.py      FAIL not running"
        exit_code=1
    fi
done

exit $exit_code

