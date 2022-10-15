# !/bin/sh

if [[ "$(docker images -q ardupilot 2> /dev/null)" == "" ]]; then
    CUR_LOC="$(pwd)"
    cd ardupilot-suas
    docker build . -t ardupilot
    cd $CUR_LOC
fi