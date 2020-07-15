#!/bin/bash
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

cd $SCRIPT_DIR

pid=$(pgrep -f "python3 api_sensors.py")
if [ $? -eq 0 ]
then
    echo $(date '+%s') api_sensors.py already running as PID $pid
else
    echo $(date '+%s') starting api_sensors.py
    nohup python3 api_sensors.py >api_sensors.log 2>api_sensors.err & disown
fi
