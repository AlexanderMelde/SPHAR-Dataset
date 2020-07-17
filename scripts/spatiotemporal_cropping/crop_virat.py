"""
Loop through and parse VIRAT annotation files, find their corresponding videos and
cut and crop them to multiple videos based action instances.

Author: Alexander Melde (alexander@melde.net)
"""

import os
import json
import glob

import cv2
from tqdm import tqdm

from cutcrop_functions import print_if, cut_and_crop

FOLDER_BASE = '../CropVIRAT'   # absolute or relative to script
FOLDER_IN = 'in'               # relative to FOLDER_BASE
FOLDER_OUT = 'out'             # relative to FOLDER_BASE
FOLDER_ANNOT = 'annot'         # relative to FOLDER_IN
FOLDER_VIDEO = 'video/ground'  # relative to FOLDER_IN
EXTENSION_VIDEO = 'mp4'        # file extension of the input videos
ENABLE_CROP = True             # Set to True to enable Cropping to Bbox
VERBOSE_OUTPUT = False         # Set to True to enable DEBUG Messages

VIRAT_CLASSES = {1: 'load_car', 2: 'unload_car', 3: 'open_car', 4: 'close_car',
                 5: 'entering_vehicle', 6: 'exiting_vehicle', 7: 'gesturing',
                 8: 'digging', 9: 'carrying', 10: 'running', 11: 'entering_facility',
                 12: 'exiting_facility'}

# Loop through annotations / for each video annotation:
activities = {}
annot_folder = os.path.join(FOLDER_BASE, FOLDER_IN, FOLDER_ANNOT)
search_pattern = os.path.join(annot_folder, '**', '*.txt')
output_video_dir = os.path.join(FOLDER_BASE, FOLDER_OUT, FOLDER_VIDEO)
for annot_filepath_full in tqdm(sorted(glob.glob(search_pattern, recursive=True)),
                                desc="Parsing Annotations and Cropping...", unit=" annots"):

    annot_filename = os.path.splitext(os.path.basename(annot_filepath_full))[0]
    video_name, annotation_type = annot_filename.split(".viratdata.")

    print_if(VERBOSE_OUTPUT, "Annotation", annot_filepath_full,
             annot_filename, video_name, annotation_type)

    if annotation_type == "events":
        if video_name not in activities.keys():
            activities[video_name] = []
        video_filepath_in = os.path.join(FOLDER_BASE, FOLDER_IN, FOLDER_VIDEO,
                                         f"virat_{video_name}.{EXTENSION_VIDEO}")

        cap = cv2.VideoCapture(video_filepath_in)
        if not cap.isOpened():
            print("WARNING could not open video (skipping)", video_filepath_in)
            continue
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        input_size = (int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
                      int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)))

        # for each event in this video
        with open(annot_filepath_full, "r") as f:
            for act_row in [line.rstrip() for line in f]:
                # parse event data to object
                act_row_values = act_row.split(" ")
                # filter duplicate entries
                if int(act_row_values[0]) not in [a['id'] for a in activities[video_name]]:
                    act = {
                        'id': int(act_row_values[0]),
                        'type': int(act_row_values[1]),
                        'timespan': (int(act_row_values[3]), int(act_row_values[4])),
                        'bbox': {
                            'x': int(act_row_values[6]),
                            'y': int(act_row_values[7]),
                            'w': int(act_row_values[8]),
                            'h': int(act_row_values[9])
                        }
                    }
                    activities[video_name].append(act)

                    act_name = VIRAT_CLASSES[act['type']]

                    cut_and_crop(mode="ffmpeg", input_video_cap=cap, input_fps=fps,
                                 input_size=input_size, input_video_name=video_name,
                                 dataset_name="virat", activity_name=VIRAT_CLASSES[act['type']],
                                 activity_id=act['id'], output_dir=output_video_dir,
                                 timespan=act['timespan'], bbox=act['bbox'], preview_video=False,
                                 crop=ENABLE_CROP, verbose_output=VERBOSE_OUTPUT)

os.makedirs(os.path.join(FOLDER_BASE, FOLDER_OUT), exist_ok=True)
with open(os.path.join(FOLDER_BASE, FOLDER_OUT, "events.json"), 'w') as f:
    json.dump(activities, f)

print("Done!")
