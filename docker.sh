#!/bin/bash
set -e -x
img=tracedisplay
docker build -t ${img} .
docker run --rm \
       -v ${ROOT:=$PWD}/TraceDisplay/examples:/home/server/TraceDisplay/examples:ro \
       -v ${ROOT:=$PWD}/TraceDisplay/examples/notebook:/home/server/TraceDisplay/examples/notebook \
       -p ${PORT:=443}:443 \
       ${img}
