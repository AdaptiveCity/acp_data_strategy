#!/bin/bash

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

cd $SCRIPT_DIR

source venv/bin/activate

$SCRIPT_DIR/api_bim/run.sh

$SCRIPT_DIR/api_readings/run.sh

$SCRIPT_DIR/api_sensors/run.sh

$SCRIPT_DIR/api_space/run.sh

$SCRIPT_DIR/api_people/run.sh

$SCRIPT_DIR/api_permissions/run.sh
$SCRIPT_DIR/api_displays/run.sh
