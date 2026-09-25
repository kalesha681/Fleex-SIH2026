#!/bin/bash
echo "Cleaning up running Gazebo and ROS 2 processes..."

# Kill Gazebo Harmonic (ruby and gz server/client)
pkill -f "gz sim"
pkill -f ruby

# Kill ros_gz_bridge and ros2 processes
pkill -f parameter_bridge
pkill -f ros2

# Clean up any generated temp URDFs
rm -f /tmp/amr*.urdf

echo "Cleanup complete!"
