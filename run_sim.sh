#!/bin/bash
source install/setup.bash
export RMW_IMPLEMENTATION=rmw_zenoh_cpp
export GZ_SIM_RESOURCE_PATH=/home/cp-lab/sih_fleex_workspace/simulation/models:$GZ_SIM_RESOURCE_PATH

# Trap Ctrl+C (SIGINT) to clean up background jobs
trap 'echo "Stopping simulation..."; kill $ZENOH_PID $GZ_PID $LAUNCH_PID 2>/dev/null; wait $ZENOH_PID $GZ_PID $LAUNCH_PID 2>/dev/null; echo "Simulation stopped cleanly."; exit 0' SIGINT

echo "Starting Zenoh Router..."
ros2 run rmw_zenoh_cpp rmw_zenohd &
ZENOH_PID=$!

echo "Starting Gazebo..."
gz sim -r simulation/worlds/large_warehouse.world &
GZ_PID=$!

echo "Starting Robot Spawner..."
ros2 launch simulation/launch/bringup.launch.py &
LAUNCH_PID=$!

# Wait for background processes so the script doesn't exit immediately
wait
