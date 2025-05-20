import unreal
import argparse
# import sys
import os
import json
# import tkinter as tk

parser = argparse.ArgumentParser(description="MetaHuman Performance to Sequence")
parser.add_argument("--raw_data_path", type=str, help="Path to raw data", default="H:\\datasets\\Fretlyn\\Face\\Fretlyn")
parser.add_argument("--level", type=str, help="Default level to open", default="Untitled")
parser.add_argument("--base_path", type=str, help="Base path to assets", default="/Game/FacialCapture/")
parser.add_argument("--identity", type=str, help="MetaHuman Identity to use", default="Fretlyn")
parser.add_argument("--capture_data_path", type=str, help="Path to capture data", default="Fretlyn_CaptureSource_Ingested/")
parser.add_argument("--start_anim", type=int, help="Start animation number", default=1)
parser.add_argument("--end_anim", type=int, help="End animation number", default=-1)
parser.add_argument("--performance_path", type=str, help="Path to performance asset", default="/Game/Performances/")
parser.add_argument("--metahuman_path", type=str, help="Path to MetaHuman", default="/Game/MetaHumans/")
parser.add_argument("--target_metahuman", type=str, help="Target MetaHuman to use", default="Bernice")
parser.add_argument("--output_path", type=str, help="Output path for animation sequence", default="H:\\datasets\\Fretlyn\\Face\\Fretlyn")

args = parser.parse_args()


def create_performance_asset(path_to_identity : str, path_to_capture_data : str, save_performance_location : str, start_frame=-1, end_frame=-1) -> unreal.MetaHumanPerformance:
    """
    Create a performance asset from the given identity and capture data.
    """
    # Load the identity and capture data assets
    print(f"Loading identity asset from {path_to_identity}")
    print(f"Loading capture data asset from {path_to_capture_data}")
    capture_data_asset = unreal.load_asset(path_to_capture_data)
    performance_asset_name = f"Performance_{capture_data_asset.get_name()}"
    if unreal.EditorAssetLibrary.does_asset_exist(f"{save_performance_location}/{performance_asset_name}"):
        print(f"Performance asset already exists at {save_performance_location}/{performance_asset_name}")
        return unreal.EditorAssetLibrary.load_asset(f"{save_performance_location}/{performance_asset_name}")
    if not capture_data_asset:
        raise ValueError(f"Capture data asset not found at {path_to_capture_data}")
    identity_asset = unreal.load_asset(path_to_identity)
    if not identity_asset:
        raise ValueError(f"Identity asset not found at {path_to_identity}")

    asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
    performance_asset = asset_tools.create_asset(asset_name=performance_asset_name, package_path=save_performance_location, 
                                                 asset_class=unreal.MetaHumanPerformance, factory=unreal.MetaHumanPerformanceFactoryNew())

    performance_asset.set_editor_property("identity", identity_asset)  # load into the identity setting
    performance_asset.set_editor_property("footage_capture_data", capture_data_asset)  # load into the capture footage setting

    if start_frame != -1:
        performance_asset.set_editor_property("start_frame_to_process", start_frame)

    if end_frame != -1:
        performance_asset.set_editor_property("end_frame_to_process", end_frame)

    #Setting process to blocking will make sure the action is executed on the main thread, blocking it until processing is finished
    process_blocking = True
    performance_asset.set_blocking_processing(process_blocking)

    unreal.log(f"Starting MH pipeline for '{animation_name}'")
    startPipelineError = performance_asset.start_pipeline()
    if startPipelineError is unreal.StartPipelineErrorType.NONE:
        unreal.log(f"Finished MH pipeline for '{animation_name}'")
    elif startPipelineError is unreal.StartPipelineErrorType.TOO_MANY_FRAMES:
        unreal.log(f"Too many frames when starting MH pipeline for '{animation_name}'")
    else:
        unreal.log(f"Unknown error starting MH pipeline for '{animation_name}'")

    return performance_asset


def export_animation(performance_asset: unreal.MetaHumanPerformance, export_sequence_location: str) -> str:
    """
    Process the shot and export the animation sequence.
    """
    animation_name = f"AS_{performance_asset.get_name()}"

    if unreal.EditorAssetLibrary.does_asset_exist(f"{export_sequence_location}/{animation_name}"):
        print(f"Animation sequence already exists at {export_sequence_location}/{animation_name}")
        return animation_name
    
    unreal.log(f"Exporting animation sequence for Performance '{animation_name}'")

    target_skeleton = unreal.load_asset("/Game/MetaHumans/Common/Face/Face_Archetype_Skeleton")
    export_settings = unreal.MetaHumanPerformanceExportAnimationSettings()
    export_settings.enable_head_movement = False # Enable or disable to export the head rotation
    export_settings.target_skeleton_or_skeletal_mesh = target_skeleton
    export_settings.show_export_dialog = False
    export_settings.export_range = unreal.PerformanceExportRange.PROCESSING_RANGE
    unreal.MetaHumanPerformanceExportUtils.export_animation_sequence(performance_asset, export_settings)
    unreal.log(f"Exported Anim Sequence {animation_name}")

    #export the animation sequence
    return animation_name


# function to get the current level sequence and the sequencer objects
def get_sequencer_objects(level_sequence):
	world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
	#sequence_asset = unreal.LevelSequenceEditorBlueprintLibrary.get_current_level_sequence()
	sequence_asset = level_sequence
	range = sequence_asset.get_playback_range()
	sequencer_objects_list = []
	sequencer_names_list = []
	bound_objects = []

	sequencer_objects_list_temp = unreal.SequencerTools.get_bound_objects(world, sequence_asset, sequence_asset.get_bindings(), range)

	for obj in sequencer_objects_list_temp:
		bound_objects = obj.bound_objects

		if len(bound_objects)>0:
			if type(bound_objects[0]) == unreal.Actor:
				sequencer_objects_list.append(bound_objects[0])
				sequencer_names_list.append(bound_objects[0].get_actor_label())
	return sequence_asset, sequencer_objects_list, sequencer_names_list


# function to export the face animation keys to a json file
def mgMetaHuman_face_keys_export(level_sequence, output_path):
	system_lib = unreal.SystemLibrary()
	# root = tk.Tk()
	# root.withdraw()

	face_anim = {}

	world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()

	sequence_asset, sequencer_objects_list,sequencer_names_list = get_sequencer_objects(level_sequence)
	face_possessable = None

	editor_asset_name = unreal.EditorAssetLibrary.get_path_name_for_loaded_asset(sequence_asset).split('.')[-1]
	
	for num in range(0, len(sequencer_names_list)):
		actor = sequencer_objects_list[num]
		asset_name = actor.get_actor_label()
		bp_possessable = sequence_asset.add_possessable(actor)
		child_possessable_list = bp_possessable.get_child_possessables()
		character_name = ''

		for current_child in child_possessable_list:
			if 'Face' in current_child.get_name():
				face_possessable = current_child
		
		if face_possessable:
			character_name = (face_possessable.get_parent().get_display_name())
			face_possessable_track_list = face_possessable.get_tracks()
			face_control_rig_track = face_possessable_track_list[len(face_possessable_track_list)-1]
			face_control_channel_list = unreal.MovieSceneSectionExtensions.get_all_channels(face_control_rig_track.get_sections()[0])
			face_control_name_list = []

			for channel in face_control_channel_list:
				channel_name = str(channel.get_name())
				channel_string_list = channel_name.split('_')
				channel_name = channel_name.replace('_' + channel_string_list[-1], '')
				face_control_name_list.append(channel_name)

			for ctrl_num in range(0, len(face_control_channel_list)):
				control_name = face_control_name_list[ctrl_num]

				try:
					numKeys = face_control_channel_list[ctrl_num].get_num_keys()
					key_list = [None] * numKeys
					keys = face_control_channel_list[ctrl_num].get_keys()
					for key in range(0, numKeys):
						key_value = keys[key].get_value()
						key_time = keys[key].get_time(time_unit=unreal.SequenceTimeUnit.DISPLAY_RATE).frame_number.value
						key_list[key]=([key_value, key_time])

					face_anim[control_name] = key_list
				except:
					face_anim[control_name] = []
			
			character_name = str(character_name)
			if 'BP_' in character_name:
				character_name = character_name.replace('BP_', '')
			if 'BP ' in character_name:
				character_name = character_name.replace('BP ', '')

			character_name = character_name.lower()
			print('character_name is ' + character_name)
            
			
			folder_path = output_path
			os.makedirs(folder_path, exist_ok=True)
			file_path = os.path.join(folder_path, f'{editor_asset_name}_face_anim.json')
			with open(file_path, 'w') as keys_file:
				# keys_file.write('anim_keys_dict = ')
				keys_file.write(json.dumps(face_anim))	
			
			print('Face Animation Keys output to: ' + str(keys_file.name))
		else:
			print(editor_asset_name)
			print('is not a level sequence. Skipping.')


#path that contains video data, start to process performance
path = args.raw_data_path #can be changed
output_order = 1
required_captures = [os.path.join(path, capture) for capture in os.listdir(path) if os.path.isdir(os.path.join(path, capture)) and int(capture.split("_")[-1]) >= args.start_anim and (args.end_anim == -1 or int(capture.split("_")[-1]) <= args.end_anim)]

print("The required captures are: ")
print(required_captures)

performance_meta = {
      "raw_data_path": None,
      "identity": None,
      "capture_data": None,
      "frames": -1,
      "performance_asset": None,
      "animation_sequence": None,
      "target_metahuman": None,
      "output_path": None,
}

performances = []

for capture_path in required_captures:
    # Get the folder number from the capture path
    meta = performance_meta.copy()
    meta["raw_data_path"] = capture_path
    meta["identity"] = os.path.join(args.base_path, args.identity)
    meta["capture_data"] = os.path.join(args.base_path, args.capture_data_path, 'Fretlyn_' + capture_path.split("_")[-1])
    json_file_path = os.path.join(capture_path, "take.json")
    with open(json_file_path, "r") as file:
        data = json.load(file)
    end_frame = data["frames"]
    meta["frames"] = end_frame
    performance_asset = create_performance_asset(
        path_to_identity=meta["identity"],
        path_to_capture_data=meta["capture_data"],
        save_performance_location=args.performance_path,
        start_frame=0,
        end_frame=meta["frames"]
    )
    meta["performance_asset"] = os.path.join(args.performance_path, performance_asset.get_name())
    print(f"Performance asset created: {meta['performance_asset']}")
    animation_name = export_animation(
        performance_asset=performance_asset,
        export_sequence_location=args.performance_path
    )
    meta["animation_sequence"] = os.path.join(args.performance_path, animation_name)
    print(f"Animation sequence created: {meta['animation_sequence']}")
    # Set the target MetaHuman
    meta["target_metahuman"] = os.path.join(args.metahuman_path, args.target_metahuman)
    meta["output_path"] = args.output_path
    performances.append(meta)
    print(performances)
print("The performance process is done!")

# The start the second part: create the level sequence and export the sequence
# add a new actor into the world
actor_path = "/Game/MetaHumans/Bernice/BP_Bernice" # the path of the actor, can be changed
actor_class = unreal.EditorAssetLibrary.load_blueprint_class(actor_path)
coordinate = unreal.Vector(-25200.0, -25200.0, 100.0) # randomly put it on a coordinate of the world
editor_subsystem = unreal.EditorActorSubsystem()
new_actor = editor_subsystem.spawn_actor_from_class(actor_class, coordinate)

animation_sequence = dict()
#assume the dataset is only 50 folders !!! Important, need to be changed base on real dataset number!! And number order should be 1, 2, 3, 4, ... ...
for i in range(1,50):
    animation_sequence[i] = False

# path = "F:\\Jerry\\Vasilisa" #folder that contain all the character folders, need to be changed based on the real path, can be changed

for meta in performances:
    frames = meta["frames"]
    #create a new level sequence
    asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
    asset_name = f"LS_{meta['performance_asset'].split('/')[-1]}"
    level_sequence = unreal.AssetTools.create_asset(asset_tools, asset_name, package_path=args.performance_path, asset_class=unreal.LevelSequence, factory=unreal.LevelSequenceFactoryNew())

    level_sequence.set_playback_start(0) #starting frame will always be 0
    level_sequence.set_playback_end(frames) #end

    anim_asset = unreal.load_asset(meta["animation_sequence"])
    params = unreal.MovieSceneSkeletalAnimationParams()
    params.set_editor_property("Animation", anim_asset)

    #add the actor into the level sequence
    actor_binding = level_sequence.add_possessable(new_actor)
    transform_track = actor_binding.add_track(unreal.MovieScene3DTransformTrack)
    anim_track = actor_binding.add_track(unreal.MovieSceneSkeletalAnimationTrack)

    # Add section to track to be able to manipulate range, parameters, or properties
    transform_section = transform_track.add_section()
    anim_section = anim_track.add_section()

    # Get level sequence start and end frame
    start_frame = level_sequence.get_playback_start()
    end_frame = level_sequence.get_playback_end()

    # Set section range to level sequence start and end frame
    transform_section.set_range(start_frame, end_frame)
    anim_section.set_range(start_frame, end_frame)

    #add face animation track
    components = new_actor.get_components_by_class(unreal.SkeletalMeshComponent)
    print(f"Components of Bernice: ")
    print(components)

    face_component = None
    for component in components:
        if component.get_name() == "Face":
            face_component = component
            break
    print(face_component)

    #get the face track (same technique as above):
    face_binding = level_sequence.add_possessable(face_component)
    print(face_binding)
    transform_track2 = face_binding.add_track(unreal.MovieScene3DTransformTrack)
    anim_track2 = face_binding.add_track(unreal.MovieSceneSkeletalAnimationTrack)
    transform_section2 = transform_track2.add_section()
    anim_section2 = anim_track2.add_section()
    anim_section2.set_editor_property("Params", params)#add animation
    transform_section2.set_range(start_frame, end_frame)
    anim_section2.set_range(start_frame, end_frame)

    # bake to control rig to the face
    print("level sequence: " + str(level_sequence))

    editor_subsystem = unreal.UnrealEditorSubsystem()
    world = editor_subsystem.get_editor_world()
    print("world: " + str(world))

    anim_seq_export_options = unreal.AnimSeqExportOption()
    print("anim_seq_export_options: " + str(anim_seq_export_options))

    control_rig = unreal.load_object(name='/Game/MetaHumans/Common/Face/Face_ControlBoard_CtrlRig', outer = None)# can be changed
    control_rig_class = control_rig.get_control_rig_class()# use class type in the under argument
    print("control rig class: " + str(control_rig_class))
    
    unreal.ControlRigSequencerLibrary.bake_to_control_rig(world, level_sequence, control_rig_class = control_rig_class, export_options = anim_seq_export_options, tolerance = 0.01, reduce_keys = False, binding = face_binding)

    # Refresh to visually see the new level sequence
    unreal.LevelSequenceEditorBlueprintLibrary.refresh_current_level_sequence()

    # Export the current face animation keys to a json file
    output_path = meta['output_path']
    mgMetaHuman_face_keys_export(level_sequence, output_path)
    unreal.LevelSequenceEditorBlueprintLibrary.refresh_current_level_sequence()

print("Well Done! Jerry!")
