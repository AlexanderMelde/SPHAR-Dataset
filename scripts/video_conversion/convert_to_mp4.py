"""
Converts videos like the following using a high-efficiency H265 HEVC Codec:

../Converting/in/livevids/VIDS/GT/grunover.avi
../Converting/in/CAVIAR/kick/kick001.mpg
to
../Converting/out/livevids/VIDS/GT/grunover.mp4
../Converting/out/CAVIAR/kick/kick001.mp4

Author: Alexander Melde (alexander@melde.net)
"""


import os
import glob
import shlex
import subprocess

from tqdm import tqdm

BASE_FOLDER = '../Converting'    # absolute or relative to script
IN_FOLDER = 'in'                 # relative to BASE_FOLDER
OUT_FOLDER = 'out'               # relative to BASE_FOLDER
IN_FILE_EXTENSION = 'avi'        # avi, mpg, MPG, mpeg, mov, mp4, MP4, ...
VERBOSE_OUTPUT = False           # Set to True to enable DEBUG Messages

folder_search_pattern = os.path.join(
    BASE_FOLDER, IN_FOLDER, '**', '*.'+IN_FILE_EXTENSION)
for video_filepath_full in tqdm(sorted(glob.glob(folder_search_pattern, recursive=True)),
                                desc="Converting Videos...", unit=" videos"):

    # generate video_filepath path relative to IN_FOLDER
    video_filepath = os.path.relpath(video_filepath_full,
                                     os.path.join(BASE_FOLDER, IN_FOLDER))

    # generate out_video filename path
    out_video_filepath_full = os.path.join(BASE_FOLDER, OUT_FOLDER,
                                           os.path.splitext(video_filepath)[0]+".mp4")

    if VERBOSE_OUTPUT:
        print("Converting", video_filepath, "to", out_video_filepath_full)

    # create output folder
    output_dir = os.path.dirname(out_video_filepath_full)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    if os.path.isfile(out_video_filepath_full):
        # if VERBOSE_OUTPUT:
        print("skipping file, already exists:", out_video_filepath_full)
    else:
        verbosity = (" -hide_banner  -loglevel error "  # -nostats
                     "-x265-params log-level=error") if not VERBOSE_OUTPUT else ""

        ffmpeg_cmd = ("ffmpeg -y -i \""+video_filepath_full + "\""
                      " -crf 24 -vcodec libx265"+verbosity+" \""+out_video_filepath_full+"\"")

        if VERBOSE_OUTPUT:
            print("using command", ffmpeg_cmd)

        # splits at space with preserved substrings
        subprocess.call(shlex.split(ffmpeg_cmd))

print("Done!")
