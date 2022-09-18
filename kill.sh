#!/bin/sh
CID=$(docker ps | grep $1 | awk '{print $1;}') && echo "${CID}"
docker stop "$CID"
docker rm "$CID"