"""
Loop through and parse MEVA annotation files, find their corresponding videos and
cut and crop them to multiple videos based on action instances.

Author: Alexander Melde (alexander@melde.net)
"""

import os
import json
import glob

import cv2
import yaml
from tqdm import tqdm

from cutcrop_functions import print_if, cut_and_crop

FOLDER_BASE = '../CropMeva'     # absolute or relative to script
FOLDER_IN = 'in'                # relative to FOLDER_BASE
FOLDER_OUT = 'out'              # relative to FOLDER_BASE
FOLDER_ANNOT = 'annot'          # relative to FOLDER_IN
FOLDER_VIDEO = 'video'          # relative to FOLDER_IN
ENABLE_CROP = True              # Set to True to enable Cropping to Bbox
VERBOSE_OUTPUT = False          # Set to True to enable DEBUG Messages

# Include old and new (revised) activity names:
RELEVANT_CLASSES = ['person_abandons_package', 'abandon_package',
                    'person_rides_bicycle', 'riding', 'Riding'
                    'person_sits_down', 'person_sitting_down',
                    'person_steals_object', 'theft', 'Theft']

# Loop through annotations / for each video annotation:
activities = {}
annot_folder = os.path.join(FOLDER_BASE, FOLDER_IN, FOLDER_ANNOT)
search_pattern = os.path.join(annot_folder, '**', '*-activities.yml')
output_video_dir = os.path.join(FOLDER_BASE, FOLDER_OUT, FOLDER_VIDEO)
for annot_file_activities in tqdm(sorted(glob.glob(search_pattern, recursive=True)),
                                  desc="Parsing Annotations and Cropping...", unit=" annots"):

    annot_name = os.path.splitext(os.path.basename(annot_file_activities))[0]

    # split on last dash
    video_name, _, annotation_type = annot_name.rpartition('-')

    print_if(VERBOSE_OUTPUT, "Annotation", annot_file_activities,
             annot_name, video_name, annotation_type)

    # get coressponding path to the input video
    annot_filepath_rel = os.path.relpath(annot_file_activities, annot_folder)
    folder_structure_rel = os.path.dirname(annot_filepath_rel)
    video_filepath_in = os.path.join(FOLDER_BASE, FOLDER_IN, FOLDER_VIDEO,
                                     folder_structure_rel, f"{video_name}.mp4")
    print_if(VERBOSE_OUTPUT, "Video", video_filepath_in)

    # get companion annot files
    annot_file_types = os.path.join(
        annot_folder, folder_structure_rel, f"{video_name}-types.yml")
    annot_file_geom = os.path.join(
        annot_folder, folder_structure_rel, f"{video_name}-geom.yml")

    # get maximum bbox of each object mentioned in geom annot
    obj_bbox = {}
    with open(annot_file_geom, "r") as f:
        f_content = f.read()
        yaml_list = yaml.load(f_content, Loader=yaml.FullLoader)
        for y_obj in yaml_list:
            if 'geom' in y_obj.keys():
                obj_id = y_obj['geom']['id1']
                frame_nr = y_obj['geom']['ts0']
                x1, y1, x2, y2 = map(int, y_obj['geom']['g0'].split())

                if obj_id not in obj_bbox.keys():
                    obj_bbox[obj_id] = dict(x=float("inf"), w=0,
                                            y=float("inf"), h=0)

                obj_bbox[obj_id] = {
                    'x': min(obj_bbox[obj_id]['x'], x1),
                    'y': min(obj_bbox[obj_id]['y'], y1),
                    'w': max(obj_bbox[obj_id]['w'], x2-x1),
                    'h': max(obj_bbox[obj_id]['h'], y2-y1)
                }

    # get activities
    activity_id = 0
    with open(annot_file_activities, "r") as f:
        f_content = f.read()
        yaml_list = yaml.load(f_content, Loader=yaml.FullLoader)
        for y_obj in yaml_list:
            if 'act' in y_obj.keys():
                act_classname = min(y_obj['act']['act2'])
                if act_classname in RELEVANT_CLASSES:
                    act_timespan = y_obj['act']['actors'][0]['timespan'][0]['tsr0']
                    act_object = y_obj['act']['id2']

                    if act_object in obj_bbox.keys():
                        act = {
                            'id': activity_id,
                            'type': act_classname,
                            'timespan': tuple(act_timespan),
                            'bbox': obj_bbox[act_object]
                        }

                        if video_name not in activities.keys():
                            activities[video_name] = []

                        activities[video_name].append(act)

                        activity_id += 1

    # now loop through those activities we found
    if video_name in activities.keys() and len(activities[video_name]) > 0:
        cap = cv2.VideoCapture(video_filepath_in)
        if not cap.isOpened():
            print("WARNING could not open video (skipping)", video_filepath_in)
            continue
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        input_size = (int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
                      int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)))

        # for each event in this video
        for act in activities[video_name]:
            cut_and_crop(mode="ffmpeg", input_video_cap=cap, input_fps=fps,
                         input_size=input_size, input_video_name=video_name,
                         dataset_name="meva", activity_name=act['type'],
                         activity_id=act['id'], output_dir=output_video_dir,
                         timespan=act['timespan'], bbox=act['bbox'], preview_video=False,
                         crop=ENABLE_CROP, verbose_output=VERBOSE_OUTPUT)


os.makedirs(os.path.join(FOLDER_BASE, FOLDER_OUT), exist_ok=True)
with open(os.path.join(FOLDER_BASE, FOLDER_OUT, "events.json"), 'w') as f:
    json.dump(activities, f)

print(f"Done! Found activities in {len(activities.keys())} videos.")
