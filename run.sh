#!/bin/bash

SOURCE_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
LOG_PATH="${SOURCE_DIR}/mya-nee.log"
DRIVER_PATH="${SOURCE_DIR}/src/drivers/mya-nee.py"

nohup unbuffer python3 $DRIVER_PATH | tee $LOG_PATH &
less +F $LOG_PATH
