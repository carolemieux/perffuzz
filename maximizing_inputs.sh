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

trace="branch_trace.log"

rm -f $trace
for input in $@; do
    AFL_LOG_LOC=$trace $prog < $input 1> /dev/null 2> /dev/null
    echo "# End $input" >> $trace
done

$SCRIPT_DIR/maximizing_inputs.py $trace

rm -f $trace


