#!/bin/bash

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

cd $SCRIPT_DIR
pid=$(pgrep -f "python3 api_displays.py")
if [ $? -eq 0 ]
then
    echo $(date '+%s') api_displays.py already running as PID $pid
    exit 1
else
    echo $(date '+%s') starting api_displays.py
    nohup python3 api_displays.py >/var/log/acp_prod/api_displays.log 2>/var/log/acp_prod/api_displays.err </dev/null & disown
    exit 0
fi
