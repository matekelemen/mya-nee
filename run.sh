#!/bin/bash

SOURCE_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
LOG_PATH="${SOURCE_DIR}"
DRIVER_PATH="${SOURCE_DIR}/src/drivers"

nohup unbuffer python3 $DRIVER_PATH/mya-nee.py | tee $LOG_PATH/mya-nee.log &
nohup unbuffer python3 $DRIVER_PATH/mya-nee-telegram.py | tee $LOG_PATH/mya-nee-telegram.log &

