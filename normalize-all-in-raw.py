# IMPORTANT:
# Run this with blender --background --python normalize-all-in-raw.py
# A custom version of Blender is installed at ~/blender-4.0.2-linux-x64/blender

import os
import bpy

BASE_DATA_PATH = '/data6/leoho/vasilisa'

def p(dirpath):
    return os.path.join(BASE_DATA_PATH, *dirpath)

def create_if_not_exist(absolute_path):
    if not os.path.exists(absolute_path):
        os.makedirs(absolute_path)
        print(f'Directory {absolute_path} created')

def blender_normalize(input_path, output_path):
    # Delete all mesh objects
    bpy.ops.object.select_all(action='DESELECT')
    bpy.ops.object.select_by_type(type='MESH')
    bpy.ops.object.delete()
    # Load the .obj file
    bpy.ops.wm.obj_import(filepath=input_path, forward_axis='Y', up_axis='Z', global_scale=(1/114))
    # Move geometry to origin
    bpy.ops.object.origin_set(type='GEOMETRY_ORIGIN', center='BOUNDS')
    # Exports the selected mesh objects
    bpy.ops.wm.obj_export(filepath=output_path, forward_axis='NEGATIVE_Z', up_axis='Y', export_materials=False)

def do_normalization():
    print('normalization start')
    
    # Create output directory if not exist
    create_if_not_exist(p(['normalized']))
    
    # Sequential
    # for date_subject in sorted(os.listdir(p(['raw']))):
    #     create_if_not_exist(p(['normalized', date_subject]))
    #     for scenario_id in sorted(os.listdir(p(['raw', date_subject]))):
    #         print('Processing ' + p([date_subject, scenario_id]))
    #         create_if_not_exist(p(['normalized', date_subject, scenario_id]))
    #         for obj in sorted(os.listdir(p(['raw', date_subject, scenario_id]))):
    #             target_obj_path = p(['raw', date_subject, scenario_id, obj])
    #             output_obj_path = p(['normalized', date_subject, scenario_id, obj])
    #             blender_normalize(target_obj_path, output_obj_path)
    #             print('Normalized ' + target_obj_path)
    
    # Parallel subjects
    date_subject = 'e'
    create_if_not_exist(p(['normalized', date_subject]))
    # all_remaining_scenarios = sorted(os.listdir(p(['raw', date_subject])))[18:]
    # input(all_remaining_scenarios)
    for scenario_id in sorted(os.listdir(p(['raw', date_subject]))):
        # if scenario_id not in all_remaining_scenarios:
            # continue
        print('Processing ' + p([date_subject, scenario_id]))
        create_if_not_exist(p(['normalized', date_subject, scenario_id]))
        for obj in sorted(os.listdir(p(['raw', date_subject, scenario_id]))):
            target_obj_path = p(['raw', date_subject, scenario_id, obj])
            output_obj_path = p(['normalized', date_subject, scenario_id, obj])
            blender_normalize(target_obj_path, output_obj_path)
            print('Normalized ' + target_obj_path) 

def main():
  do_normalization()

if __name__ == '__main__':
  main()