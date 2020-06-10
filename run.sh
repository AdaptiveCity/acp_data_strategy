#!/bin/bash

SCRIPT_DIR="$( cd "$( dirname "$0" )" && pwd )"

cd $SCRIPT_DIR

pid=$(pgrep -f "python3 bim_api.py")
if [ $? -eq 0 ]
then
    echo $(date '+%s') bim_api.py already running as PID $pid
else
    echo $(date '+%s') starting bim_api.py
    nohup python3 bim_api.py >bim_api.log 2>bim_api.err </dev/null & disown
fi

pid=$(pgrep -f "python3 sensors_api.py")
if [ $? -eq 0 ]
then
    echo $(date '+%s') sensors_api.py already running as PID $pid
    exit 1
else
    echo $(date '+%s') starting sensors_api.py
    nohup python3 sensors_api.py >sensors_api.log 2>sensors_api.err </dev/null & disown
    exit 0
fi