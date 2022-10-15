# !/bin/sh

if [[ "$(docker images -q ardupilot 2> /dev/null)" != "" ]]; then
    CUR_LOC="$(pwd)"
    cd ardupilot-suas
    docker run --rm -it -v `pwd`:/ardupilot ardupilot:latest sh -c 'git submodule update --init --recursive; sudo pip install -U future lxml pymavlink mavproxy pexpect pygame intelhex; cd ArduPlane; sim_vehicle.py --map --console'
    cd $CUR_LOC
fi