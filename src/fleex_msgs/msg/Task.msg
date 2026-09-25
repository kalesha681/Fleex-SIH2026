string task_id

# Task definition
string pickup_location
string dropoff_location

# State constants
uint8 STATE_UNASSIGNED=0
uint8 STATE_ASSIGNED=1
uint8 STATE_IN_PROGRESS=2
uint8 STATE_COMPLETED=3
uint8 STATE_FAILED=4

uint8 state

# The ID of the robot assigned to this task (empty if unassigned)
string owner_id
