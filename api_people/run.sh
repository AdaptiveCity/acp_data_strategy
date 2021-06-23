#!/bin/bash

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

cd $SCRIPT_DIR
pid=$(pgrep -f "python3 api_people.py")
if [ $? -eq 0 ]
then
    echo $(date '+%s') api_people.py already running as PID $pid
    exit 1
else
    echo $(date '+%s') starting api_people.py
    nohup python3 api_people.py >/var/log/acp_prod/api_people.log 2>/var/log/acp_prod/api_people.err </dev/null & disown
    exit 0
fi
