#!/bin/bash

pushd `dirname $0` > /dev/null
SCRIPT_DIR=`pwd`
popd > /dev/null

if [ $# -lt 2 ]; then
    echo "Usage: $0 TARGET_PROGRAM_CMD INPUTS..."
    exit 1
fi

prog=$1
shift

# Gonna use a named FIFO pipe for logging to avoid disk usage
trace="branch_trace.log"
rm -f $trace
mkfifo $trace

# Opens the pipe for reading and waits in the background
$SCRIPT_DIR/maximizing_inputs.py $trace &

# Run all inputs and log branches in the pipe
for input in $@; do
    AFL_LOG_LOC=$trace $prog < $input 1> /dev/null 2> /dev/null
    echo "# End $input" >> $trace
done  > $trace # This loops writes nothing but keeps the pipe open long enough

# Cleanup
rm -f $trace


