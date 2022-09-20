#!/bin/sh
CID=$(docker ps -a | grep $1 | awk '{print $1;}')
docker stop "$CID"
docker rm "$CID"