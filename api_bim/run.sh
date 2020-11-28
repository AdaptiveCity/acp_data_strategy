#!/bin/bash

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

cd $SCRIPT_DIR
pid=$(pgrep -f "python3 api_bim.py")
if [ $? -eq 0 ]
then
    echo $(date '+%s') api_bim.py already running as PID $pid
    exit 1
else
    echo $(date '+%s') starting api_bim.py
    nohup python3 api_bim.py >/var/log/acp_prod/api_bim.log 2>/var/log/acp_prod/api_bim.err </dev/null & disown
    exit 0
fi
