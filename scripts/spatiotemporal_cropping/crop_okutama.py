"""
Loop through and parse Okutama annotation files, find their corresponding videos and
cut and crop them to multiple videos based on action instances.

Author: Alexander Melde (alexander@melde.net)
"""

import os
import json
import glob

import cv2
from tqdm import tqdm

from cutcrop_functions import print_if, cut_and_crop

FOLDER_BASE = '../CropOkutama'  # absolute or relative to script
FOLDER_IN = 'in'                # relative to FOLDER_BASE
FOLDER_OUT = 'out'              # relative to FOLDER_BASE
FOLDER_ANNOT = 'annot'          # relative to FOLDER_IN
FOLDER_VIDEO = 'video'          # relative to FOLDER_IN
EXTENSION_VIDEO = 'mp4'         # file extension of the input videos
ENABLE_CROP = True              # Set to True to enable Cropping to Bbox
VERBOSE_OUTPUT = False          # Set to True to enable DEBUG Messages

# Loop through annotations / for each video annotation:
activities = {}
annot_folder = os.path.join(FOLDER_BASE, FOLDER_IN, FOLDER_ANNOT)
search_pattern = os.path.join(annot_folder, '**', '*.txt')
output_video_dir = os.path.join(FOLDER_BASE, FOLDER_OUT, FOLDER_VIDEO)
for annot_filepath_full in tqdm(sorted(glob.glob(search_pattern, recursive=True)),
                                desc="Parsing Annotations and Cropping...", unit=" annots"):

    video_name = os.path.splitext(os.path.basename(annot_filepath_full))[0]

    print_if(VERBOSE_OUTPUT, "Annotation", annot_filepath_full, video_name)

    if video_name not in activities.keys():
        activities[video_name] = []

    video_filepath_in = os.path.join(FOLDER_BASE, FOLDER_IN, FOLDER_VIDEO,
                                     f"{video_name}.{EXTENSION_VIDEO}")

    cap = cv2.VideoCapture(video_filepath_in)
    if not cap.isOpened():
        print("WARNING could not open video (skipping)", video_filepath_in)
        continue
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    input_size = (int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
                  int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)))

    # loop through each event frame in this video and aggregate
    # information to get from frame- to tube-level annotations
    event_bboxes = {}
    with open(annot_filepath_full, "r") as f:
        for act_row in [line.rstrip() for line in f]:
            # parse event frame data to object
            act_row_values = act_row.split(" ")

            if len(act_row_values) > 10:
                act_type = ''.join([e for e in act_row_values[10] if e.isalnum()])
            else:
                act_type = "None"

            act_id = int(act_row_values[0])
            frame_nr = int(act_row_values[5])
            x1, y1, x2, y2 = map(int, act_row_values[1:5])

            # get surrounding bbox tube and time range
            if act_id not in event_bboxes.keys():
                event_bboxes[act_id] = dict(x1=float("inf"), x2=0,
                                            y1=float("inf"), y2=0,
                                            ts=float("inf"), te=0)
            
            event_bboxes[act_id] = {
                'type': act_type,
                'x1': min(event_bboxes[act_id]['x1'], x1),
                'y1': min(event_bboxes[act_id]['y1'], y1),
                'x2': max(event_bboxes[act_id]['x2'], x2),
                'y2': max(event_bboxes[act_id]['y2'], y2),
                'ts': min(event_bboxes[act_id]['ts'], frame_nr),
                'te': max(event_bboxes[act_id]['te'], frame_nr)
            }

            # print(event_bboxes[act_id], x1, y1, x2, y2)

    # for each activity
    for act_id, act_info in event_bboxes.items():
        act = {
            'id': act_id,
            'type': act_info['type'],
            'timespan': (act_info['ts'], act_info['te']),
            'bbox': {
                'x': act_info['x1'],
                'y': act_info['y1'],
                'w': act_info['x2'] - act_info['x1'],
                'h': act_info['y2'] - act_info['y1']
            }
        }
        activities[video_name].append(act)

        cut_and_crop(mode="ffmpeg", input_video_cap=cap, input_fps=fps,
                     input_size=input_size, input_video_name=video_name,
                     dataset_name="okutama", activity_name=act['type'],
                     activity_id=act['id'], output_dir=output_video_dir,
                     timespan=act['timespan'], bbox=act['bbox'], preview_video=False,
                     crop=ENABLE_CROP, verbose_output=VERBOSE_OUTPUT)

os.makedirs(os.path.join(FOLDER_BASE, FOLDER_OUT), exist_ok=True)
with open(os.path.join(FOLDER_BASE, FOLDER_OUT, "events.json"), 'w') as f:
    json.dump(activities, f)

print("Done!")
