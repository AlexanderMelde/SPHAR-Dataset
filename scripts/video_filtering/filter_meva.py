"""
Find videos that contain certain classes by parsing MEVA dataset annotation files
recusively in a given folder, and save the lists of video and annotation filepaths
to files that looks like this:

2018-03-11/16/2018-03-11.16-35-01.16-40-01.school.G638.avi
2018-03-11/16/2018-03-11.16-35-08.16-40-08.hospital.G436.avi
2018-03-11/16/2018-03-11.16-40-00.16-45-00.school.G299.avi
2018-03-11/16/2018-03-11.16-40-00.16-45-00.school.G330.avi
2018-03-11/16/2018-03-11.16-45-00.16-50-00.school.G299.avi
...

Author: Alexander Melde (alexander@melde.net)
"""

import os
import glob

from tqdm import tqdm

FOLDER_ANNOT = '../ParseAnnot'  # absolute or relative to the annotation files
EXTENSION_VIDEO = 'avi'
EXTENSION_ANNOT = 'yml'
OUT_FILENAME_VIDEO = '../filter_meva_list.txt'
OUT_FILENAME_ANNOT = '../filter_meva_list_annot.txt'

# Include old and new (revised) activity names:
RELEVANT_CLASSES = ['person_abandons_package', 'abandon_package',
                    'person_rides_bicycle', 'riding', 'Riding'
                    'person_sits_down', 'person_sitting_down',
                    'person_steals_object', 'theft', 'Theft']

# Loop through annotations and filter annotation files containg relevant class names
found_video_files = []
found_annot_files = []
search_pattern = os.path.join(FOLDER_ANNOT, '**', '*.' + EXTENSION_ANNOT)
for annot_filepath_full in tqdm(sorted(glob.glob(search_pattern, recursive=True)),
                                desc="Filtering Videos...", unit=" annots"):
    filename = os.path.basename(annot_filepath_full)
    if "activities" in filename:
        with open(annot_filepath_full, "r") as f:
            f_content = f.read()
            if any(r_class in f_content for r_class in RELEVANT_CLASSES):
                drop_date = filename.split(".")[0]
                drop_sub_nr = filename.split(".")[2][0:2]
                vid_filename = (filename.split("activities")[0][:-1]
                                + "." + EXTENSION_VIDEO)
                vid_path = os.path.join(drop_date, drop_sub_nr, vid_filename)
                found_video_files.append(vid_path)
                found_annot_files.append(annot_filepath_full)

# Write list of relevant videos to a file
with open(OUT_FILENAME_VIDEO, 'w') as f:
    f.write('\n'.join(found_video_files))

with open(OUT_FILENAME_ANNOT, 'w') as f:
    f.write('\n'.join(found_annot_files))

# Print summary
print("Done! Found relevant classes in", len(found_video_files),
      "files, wrote lists to", OUT_FILENAME_VIDEO, "and", OUT_FILENAME_ANNOT)
