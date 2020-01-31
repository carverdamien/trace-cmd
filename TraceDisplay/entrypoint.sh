#!/bin/bash
set -e
while echo ; do :;done | openssl req -x509 -nodes -days 365 -newkey rsa:2048 -keyout mykey.key -out mycert.pem
jupyter-notebook --allow-root --port=443 --ip=0.0.0.0 --certfile=mycert.pem --keyfile=mykey.key
