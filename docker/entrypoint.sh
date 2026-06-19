#!/usr/bin/env bash

source /opt/ros/humble/setup.bash

if [ $# -gt 0 ];then
    # If we passed a command, run it
    exec "$@"
else
    /bin/bash
fi