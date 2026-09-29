#!/bin/bash
source /opt/ros/jazzy/setup.bash
source install/setup.bash
export RMW_IMPLEMENTATION=rmw_zenoh_cpp
echo "✅ Environment sourced. Zenoh RMW enabled."
