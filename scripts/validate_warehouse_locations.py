#!/usr/bin/env python3

import os
import yaml
import re
import sys

def main():
    workspace_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    yaml_path = os.path.join(workspace_dir, 'config', 'warehouse', 'locations.yaml')
    world_path = os.path.join(workspace_dir, 'simulation', 'worlds', 'large_warehouse.world')
    
    # 1. Read locations.yaml
    if not os.path.exists(yaml_path):
        print(f"FAIL: {yaml_path} does not exist.")
        sys.exit(1)
        
    with open(yaml_path, 'r') as f:
        data = yaml.safe_load(f)
        
    locations = data.get('locations', {})
    if not locations:
        print("FAIL: No locations found in locations.yaml")
        sys.exit(1)
        
    # 2. Read world file to get actual model names
    if not os.path.exists(world_path):
        print(f"FAIL: {world_path} does not exist.")
        sys.exit(1)
        
    with open(world_path, 'r') as f:
        world_content = f.read()
        
    world_models = set(re.findall(r'<name>(.*?)</name>', world_content))
    
    errors = 0
    
    # 3. Validate each location
    for loc_id, loc_data in locations.items():
        print(f"Validating {loc_id}...")
        
        # Check model existence
        model_id = loc_data.get('model_id')
        if not model_id:
            print(f"  ERROR: {loc_id} missing model_id")
            errors += 1
        elif model_id not in world_models and not model_id.startswith('open_space_'):
            print(f"  ERROR: Model '{model_id}' does not exist in Gazebo world!")
            errors += 1
            
        # Check frame
        if 'frame' not in loc_data:
            print(f"  ERROR: {loc_id} missing frame")
            errors += 1
            
        # Check pose and approach
        for pose_type in ['pose', 'approach']:
            p = loc_data.get(pose_type)
            if not p:
                print(f"  ERROR: {loc_id} missing {pose_type}")
                errors += 1
                continue
                
            for coord in ['x', 'y', 'yaw']:
                if coord not in p:
                    print(f"  ERROR: {loc_id} {pose_type} missing {coord}")
                    errors += 1
                elif not isinstance(p[coord], (int, float)):
                    print(f"  ERROR: {loc_id} {pose_type} {coord} is not numeric")
                    errors += 1

    if errors == 0:
        print("\nSUCCESS: All locations validated successfully.")
        sys.exit(0)
    else:
        print(f"\nFAIL: {errors} errors found in location registry.")
        sys.exit(1)

if __name__ == '__main__':
    main()
