#!/bin/bash

if [ -z "$1" ]
then
  echo Usage: ./restore.sh '<filename>.sql'
  echo 'You probably need to stop the data APIs first (acp_data_strategy/stop.sh)'
  echo 'and restart with acp_data_strategy/run.sh'
  exit 1
fi

psql acp_prod <$1

