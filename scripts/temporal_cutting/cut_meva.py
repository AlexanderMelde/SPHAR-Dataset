"""
Loop through and parse MEVA annotation files, find their corresponding videos and
cut them to multiple videos based on relevant action instances.

This file is not as well refactored as the cropping scripts, when developing with
this, i would recommend starting with the crop_xxxxxx.py scripts.

Author: Alexander Melde (alexander@melde.net)
"""

import os
import glob
import shlex
import subprocess

import cv2
import yaml
from tqdm import tqdm

FOLDER_BASE = '../CutMeva' # absolute or relative to script
FOLDER_IN = 'in'           # relative to FOLDER_BASE
FOLDER_OUT = 'out'         # relative to FOLDER_BASE
FOLDER_ANNOT = 'annot'     # relative to FOLDER_IN
FOLDER_VIDEO = 'video'     # relative to FOLDER_IN
EXTENSION_VIDEO = 'mp4'    # file extension of the input videos
VERBOSE_OUTPUT = False     # Set to True to enable DEBUG Messages

# Include old and new (revised) activity names:
RELEVANT_CLASSES = ['person_abandons_package', 'abandon_package',
                    'person_rides_bicycle', 'riding', 'Riding'
                    'person_sits_down', 'person_sitting_down',
                    'person_steals_object', 'theft', 'Theft']


def print_verbose(*args):
    """ shortcut to print only if VERBOSE_OUTPUT=True """
    if VERBOSE_OUTPUT:
        print(*args)


def merge(timespans):
    """ merge overlapping timespans, https://stackoverflow.com/q/5679638

        [(1, 5), (2, 4), (3, 6)] --->  [(1,6)]
        [(1, 3), (2, 4), (5, 8)] --->  [(1, 4), (5,8)]
    """
    timespans = sorted(timespans, key=lambda x: x[0])
    saved = list(timespans[0])
    for start, end in sorted([sorted(t) for t in timespans]):
        if start <= saved[1]:
            saved[1] = max(saved[1], end)
        else:
            yield tuple(saved)
            saved[0] = start
            saved[1] = end
    yield tuple(saved)


# Loop through annotations and filter annotation files containg relevant class names
annot_folder = os.path.join(FOLDER_BASE, FOLDER_IN, FOLDER_ANNOT)
search_pattern = os.path.join(annot_folder, '**', '*.yml')
for annot_filepath_full in tqdm(sorted(glob.glob(search_pattern, recursive=True)),
                                desc="Parsing Annotations...", unit=" annots"):
    print_verbose("Annotation", annot_filepath_full)
    with open(annot_filepath_full, "r") as f:
        f_content = f.read()
        activity_list = yaml.load(f_content, Loader=yaml.FullLoader)

        # get video name and path
        video_name_avi = activity_list.pop(0)["meta"]
        video_name_new = ("meva_" + os.path.splitext(video_name_avi)[0]
                          + "." + EXTENSION_VIDEO)
        annot_filepath_rel = os.path.relpath(annot_filepath_full, annot_folder)
        folder_structure_rel = os.path.dirname(annot_filepath_rel)
        video_filepath_in = os.path.join(FOLDER_BASE, FOLDER_IN, FOLDER_VIDEO,
                                         folder_structure_rel, video_name_new)
        print_verbose("Video", video_filepath_in)

        # find relevant frame timespans by looping over all activities
        act_timespans = {}
        for act in activity_list:
            if 'act' in act.keys():
                act_classname = min(act['act']['act2'])
                if act_classname in RELEVANT_CLASSES:
                    act_timespan = act['act']['actors'][0]['timespan'][0]['tsr0']
                    if act_classname not in act_timespans.keys():
                        act_timespans[act_classname] = []
                    act_timespans[act_classname].append(act_timespan)
        act_timespans_merged = {k: list(merge(v))
                                for k, v in act_timespans.items()}
        print_verbose("Found Timestamps", act_timespans_merged)

        # cut video to frames (for all activites and timespans)
        for act_name, act_timespans in act_timespans_merged.items():
            cap = cv2.VideoCapture(video_filepath_in)
            if not cap.isOpened():
                print("WARNING could not open video (skipping)", video_filepath_in)
                continue
            fps = int(cap.get(cv2.CAP_PROP_FPS))
            size = (int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
                    int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)))
            video_name_out = ("meva_" + os.path.splitext(video_name_avi)[0]
                              + "_" + act_name + "_%d." + EXTENSION_VIDEO)
            video_dir_out = os.path.join(FOLDER_BASE, FOLDER_OUT, act_name)
            os.makedirs(video_dir_out, exist_ok=True)

            for idx, timespan in enumerate(act_timespans):
                outfile = os.path.join(video_dir_out, video_name_out % idx)
                if os.path.isfile(outfile):
                    print("skipping file, already exists:", outfile)
                else:
                    # out = cv2.VideoWriter(outfile,
                    #                       cv2.VideoWriter_fourcc(*'mp4'), fps, size)
                    verbosity = (" -hide_banner -loglevel error "
                                 "-x265-params log-level=error") if not VERBOSE_OUTPUT else ""

                    ffmpeg_cmd = (f'/usr/bin/ffmpeg -y -s {size[0]}x{size[1]} -pixel_format'
                                  + f' bgr24 -f rawvideo -r {fps} -i pipe: -vcodec libx265'
                                  + f' -pix_fmt yuv420p -crf 24{verbosity} "{outfile}"')

                    print_verbose("now cutting to", outfile,
                                  "using cmd", ffmpeg_cmd)

                    process = subprocess.Popen(shlex.split(
                        ffmpeg_cmd), stdin=subprocess.PIPE)

                    cap.set(cv2.CAP_PROP_POS_FRAMES, timespan[0])
                    frameReturned = True
                    while cap.isOpened() and frameReturned:  # and out.isOpened():
                        frameReturned, frame = cap.read()
                        frame_number = cap.get(cv2.CAP_PROP_POS_FRAMES) - 1
                        if frame_number < timespan[1]:
                            # out.write(frame)
                            # Write raw video frame to input stream of ffmpeg sub-process.
                            process.stdin.write(frame.tobytes())
                        else:
                            break
                    # out.release()

                    process.stdin.close()  # Close and flush stdin
                    process.wait()         # Wait for sub-process to finish
                    process.terminate()    # Terminate the sub-process

print("Done!")

# print(yaml.dump(yaml_list))
