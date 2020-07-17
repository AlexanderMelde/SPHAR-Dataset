"""
Loop through and parse UCF-Aerial annotation files, find their corresponding videos and
cut and crop them to multiple videos based on relevant action instances.

Author: Alexander Melde (alexander@melde.net)
"""

import os
import json
import glob
from collections import OrderedDict

import cv2
import xmltodict
from tqdm import tqdm

from cutcrop_functions import print_if, cut_and_crop

FOLDER_BASE = '../CropUcaerial'  # absolute or relative to script
FOLDER_IN = 'in'                 # relative to FOLDER_BASE
FOLDER_OUT = 'out'               # relative to FOLDER_BASE
FOLDER_ANNOT = 'annot'           # relative to FOLDER_IN
FOLDER_VIDEO = 'video'           # relative to FOLDER_IN
EXTENSION_VIDEO = 'mpg'          # file extension of the input videos
ENABLE_CROP = True               # Set to True to enable Cropping to Bbox
VERBOSE_OUTPUT = True            # Set to True to enable DEBUG Messages

# List of all activity names to:extract the correct XGTF `attributes`
CLASSES = ['Standing', 'Walking', 'Running', 'Digging', 'Gesturing', 'Carrying',
           'Opening a Trunk', 'Closing a Trunk', 'Getting Into a Vehicle',
           'Getting Out of a Vehicle', 'Loading a Vehicle', 'Unloading a Vehicle',
           'Entering a Facility', 'Exiting a Facility']

# Loop through annotations
video_annots = {}
annot_folder = os.path.join(FOLDER_BASE, FOLDER_IN, FOLDER_ANNOT)
search_pattern = os.path.join(annot_folder, '**', '*.xgtf')
for annot_filepath_full in tqdm(sorted(glob.glob(search_pattern, recursive=True)),
                                desc="Parsing Annotations...", unit=" annots"):
    print_if(VERBOSE_OUTPUT, "Annotation", annot_filepath_full)
    with open(annot_filepath_full, "r") as f:
        f_content = f.read()
        result = xmltodict.parse(f_content)
        config = result['viper']['config']['descriptor']
        vid_filename = os.path.basename(
            result['viper']['data']['sourcefile']['@filename'])
        print_if(VERBOSE_OUTPUT, vid_filename)
        objects_xml = result['viper']['data']['sourcefile']['object']
        #print("config", config)
        objects = []
        for ox in objects_xml:
            if ox['@name'] == "PERSON" or (ox['@name'] == "object"
                                           and ox['attribute'][0]['data:svalue']['@value']
                                           == "man"):
                bboxes = {}
                activities = {}
                for attribute in ox['attribute']:
                    if attribute['@name'] in ("Location", "bounding_box"):
                        if 'data:bbox' in attribute.keys():
                            for bbox in attribute['data:bbox']:
                                if isinstance(bbox, OrderedDict):
                                    timespan = tuple(
                                        map(int, bbox['@framespan'].split(":")))
                                    for frame_nr in range(timespan[0], timespan[1]+1):
                                        bboxes[frame_nr] = {
                                            'x': int(bbox['@x']),
                                            'y': int(bbox['@y']),
                                            'w': int(bbox['@width']),
                                            'h': int(bbox['@height'])
                                        }
                    elif attribute['@name'] in CLASSES:
                        if 'data:bvalue' in attribute.keys():
                            if attribute['@name'] not in activities.keys():
                                activities[attribute['@name']] = []

                            activity_instances = attribute['data:bvalue']
                            if not isinstance(activity_instances, list):
                                activity_instances = [activity_instances]
                            for ai in activity_instances:
                                timespan = tuple(
                                    map(int, ai['@framespan'].split(":")))
                                activities[attribute['@name']].append(timespan)
                objects.append({
                    'id': ox['@id'],
                    # 'timespan': tuple(map(int, ox['@framespan'].split(":"))),
                    'bboxes': bboxes,
                    'activities': activities
                })

        if vid_filename not in video_annots.keys():
            video_annots[vid_filename] = []
        video_annots[vid_filename] = objects

        #print("data for ",vid_filename, len(objects), objects)

video_dir_out = os.path.join(FOLDER_BASE, FOLDER_OUT)

# now cut / crop video
for vid_name, vid_objs in tqdm(video_annots.items(), desc="Cutting Videos...", unit=" videos"):
    print_if(VERBOSE_OUTPUT, vid_name)
    video_filepath_in = os.path.join(
        FOLDER_BASE, FOLDER_IN, FOLDER_VIDEO, vid_name)
    input_video_name = os.path.splitext(vid_name)[0]
    cap = cv2.VideoCapture(video_filepath_in)
    if not cap.isOpened():
        print("WARNING could not open video (skipping)", video_filepath_in)
        continue
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    input_size = (int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
                  int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)))
    # for each object (e.g. person)
    for o in vid_objs:
        # for each activity
        for act_name, act_timespans in o['activities'].items():
            # for each activity instance
            for tid, timespan in enumerate(act_timespans):
                # calculate crop size for bounding boxe tube
                crop_bbox = dict(x=float("inf"), w=0,
                                 y=float("inf"), h=0)

                for frameid, frame_bbox in o['bboxes'].items():
                    crop_bbox = {
                        'x': min(crop_bbox['x'], frame_bbox['x']),
                        'w': max(crop_bbox['w'], frame_bbox['w']),
                        'y': min(crop_bbox['y'], frame_bbox['y']),
                        'h': max(crop_bbox['h'], frame_bbox['h'])
                    }

                print_if(VERBOSE_OUTPUT, "found action", act_name, "for object",
                         o['id'], "in time", timespan, "on positions", crop_bbox)

                # init video writing
                cut_and_crop(mode="ffmpeg", input_video_cap=cap, input_fps=fps,
                             input_size=input_size, input_video_name=input_video_name,
                             dataset_name="ucaerial", activity_name=act_name,
                             activity_id=tid, output_dir=video_dir_out,
                             timespan=timespan, bbox=crop_bbox,
                             preview_video=False, crop=ENABLE_CROP, verbose_output=VERBOSE_OUTPUT)


os.makedirs(os.path.join(FOLDER_BASE, FOLDER_OUT), exist_ok=True)
with open(os.path.join(FOLDER_BASE, FOLDER_OUT, "annotations.json"), 'w') as f:
    json.dump(video_annots, f)


print("Done!")
