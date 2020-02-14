#!/bin/bash
set -e -x
img=tracedisplay
docker build -t ${img} .
# Set PUBLISH_NEO4J=' ' to avoid publishing ports
: ${PUBLISH_NEO4J:=-p 7474:7474 -p 7687:7687}
docker run --name neo4j \
       --rm -d \
       ${PUBLISH_NEO4J} \
       neo4j
docker run --name ${img} \
       --link neo4j \
       --rm -d \
       -v ${ROOT:=$PWD}/TraceDisplay/examples:/home/server/TraceDisplay/examples:ro \
       -v ${ROOT:=$PWD}/TraceDisplay/examples/notebook:/home/server/TraceDisplay/examples/notebook \
       -p ${PORT:=443}:443 \
       ${img}
