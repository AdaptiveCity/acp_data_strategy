#!/bin/bash

# A simple test script to see if ACP data api processes are running

names=( api_bim api_sensors api_readings api_space)

#echo ${names[@]}
exit_code=0

# Find the length of the longest name (for print column alignment later)
max_length=1
for name in ${names[@]}
do
    if (( ${#name} > $max_length ))
    then
        max_length=${#name}
    fi
done
#echo max_Length ${max_length}

# Finally, use names for "pgrep" command to find PID's
for name in ${names[@]}
do
    # For column layout, make print name fixed width
    print_name="${name}                     " # add padding spaces
    print_name=${print_name:0:max_length}     # truncate to fixed width
    pid=$(pgrep -f "bin/python3.*${name}")
    if [ $? -eq 0 ]
    then
        echo $(date '+%s.%3N') "${print_name} OK running as PID $pid"
    else
        echo $(date '+%s.%3N') "${print_name} FAIL not running"
        exit_code=1
    fi
done

exit $exit_code
