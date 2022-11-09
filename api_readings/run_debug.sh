#!/bin/bash

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

cd $SCRIPT_DIR
pid=$(pgrep -f "python3 api_readings.py")
if [ $? -eq 0 ]
then
    echo $(date '+%s') api_readings.py already running as PID $pid
else
    echo $(date '+%s') starting api_readings.py
   # nohup python3 api_readings.py >/var/log/acp_prod/api_readings.log 2>/var/log/acp_prod/api_readings.err & disown
    python3 api_readings.py >/var/log/acp_prod/api_readings.log 2>/var/log/acp_prod/api_readings.err 

fi
