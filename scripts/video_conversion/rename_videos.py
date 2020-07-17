"""
Renames videos like the following to append dataset names to filenames:

../Renaming/in/livevids/VIDS/GT/grunover.mp4
../Renaming/in/CAVIAR/kick/kick001.mp4
to
../Renaming/out/livevids/VIDS/GT/livevids_grunover.mp4
../Renaming/out/CAVIAR/kick/CAVIAR_kick001.mp4

Author: Alexander Melde (alexander@melde.net)
"""

import os
import glob
from shutil import copyfile

from tqdm import tqdm

BASE_FOLDER = '../Renaming'      # absolute or relative to script
IN_FOLDER = 'in'                 # relative to BASE_FOLDER
OUT_FOLDER = 'out'               # relative to BASE_FOLDER
IN_FILE_EXTENSION = 'mp4'        # file extension of the videos
VERBOSE_OUTPUT = False           # Set to True to enable DEBUG Messages

folder_search_pattern = os.path.join(
    BASE_FOLDER, IN_FOLDER, '**', '*.'+IN_FILE_EXTENSION)
for video_filepath_full in tqdm(sorted(glob.glob(folder_search_pattern, recursive=True)),
                                desc="Renaming Videos...", unit=" videos"):

    # generate video_filepath path relative to IN_FOLDER
    video_filepath = os.path.relpath(video_filepath_full,
                                     os.path.join(BASE_FOLDER, IN_FOLDER))

    # get dataset name based on path
    dataset_name = video_filepath.split(os.path.sep)[0]

    # split video_filepath into path and name
    video_filepath_path, video_name = os.path.split(video_filepath)

    # generate out_video filename path
    out_video_filepath_full = os.path.join(BASE_FOLDER, OUT_FOLDER, video_filepath_path,
                                           dataset_name+"_"+video_name)

    if VERBOSE_OUTPUT:
        print("Renaming", video_filepath, "to", out_video_filepath_full)

    # create output folder
    output_dir = os.path.dirname(out_video_filepath_full)
    os.makedirs(output_dir, exist_ok=True)

    # Copy to new (renamed) location
    copyfile(video_filepath_full, out_video_filepath_full)

print("Done!")
