#!/bin/bash

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

cd $SCRIPT_DIR
pid=$(pgrep -f "python3 api_space.py")
if [ $? -eq 0 ]
then
    echo $(date '+%s') api_space.py already running as PID $pid
    exit 1
else
    echo $(date '+%s') starting api_space.py
    nohup python3 api_space.py >/var/log/acp_prod/api_space.log 2>/var/log/acp_prod/api_space.err </dev/null & disown
    exit 0
fi
