#!/bin/bash
source install/setup.bash
export GZ_SIM_RESOURCE_PATH=/home/cp-lab/sih_fleex_workspace/simulation/models:$GZ_SIM_RESOURCE_PATH

# Trap Ctrl+C (SIGINT) to clean up background jobs
trap 'echo "Stopping simulation..."; kill $GZ_PID $LAUNCH_PID 2>/dev/null; wait $GZ_PID $LAUNCH_PID 2>/dev/null; echo "Simulation stopped cleanly."; exit 0' SIGINT

echo "Starting Gazebo..."
gz sim simulation/worlds/large_warehouse.world &
GZ_PID=$!

echo "Starting Robot Spawner..."
ros2 launch simulation/launch/bringup.launch.py &
LAUNCH_PID=$!

# Wait for background processes so the script doesn't exit immediately
wait
