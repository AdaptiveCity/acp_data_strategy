#!/bin/bash

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

cd $SCRIPT_DIR
pid=$(pgrep -f "python3 api_permissions.py")
if [ $? -eq 0 ]
then
    echo $(date '+%s') api_permissions.py already running as PID $pid
else
    echo $(date '+%s') starting api_permissions.py
    nohup python3 api_permissions.py >/var/log/acp_prod/api_permissions.log 2>/var/log/acp_prod/api_permissions.err & disown
fi
