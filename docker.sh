#!/bin/bash
set -e -x
img=trace-display
docker build -t ${img} .
docker run --rm \
       -v ${ROOT:=$PWD}/trace-display/examples:/home/server/trace-display/examples:ro \
       -v ${ROOT:=$PWD}/trace-display/examples/notebook:/home/server/trace-display/examples/notebook \
       -p ${PORT:=443}:443 \
       ${img}
