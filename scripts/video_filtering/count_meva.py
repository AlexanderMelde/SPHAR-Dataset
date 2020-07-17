"""
Prints a list of action classes and the number of videos in which they occur
by parsing MEVA dataset annotation files recusively in a given folder.

Example Output: {'person_sits_down': 33, 'person_rides_bicycle': 2}

Author: Alexander Melde (a.melde@enbw.com)
"""

import os
import glob

from tqdm import tqdm

ANNOT_FOLDER = '../ParseAnnot'  # absolute or relative to the annotation files
ANNOT_EXTENSION = 'yml'
VIDEO_EXTENSION = 'avi'

# Include old and new (revised) activity names:
RELEVANT_CLASSES = ['person_abandons_package', 'abandon_package',
                    'person_rides_bicycle', 'riding', 'Riding'
                    'person_sits_down', 'person_sitting_down',
                    'person_steals_object', 'theft', 'Theft']

# Loop through all annotation files and count occurences of each class
class_counts = {}
folder_search_pattern = os.path.join(
    ANNOT_FOLDER, '**', '*.' + ANNOT_EXTENSION)
for annot_filepath in tqdm(sorted(glob.glob(folder_search_pattern, recursive=True)),
                           desc="Counting Class Occurrences...", unit=" annot. files"):
    filename = os.path.basename(annot_filepath)
    if "activities" in filename:
        with open(annot_filepath, "r") as f:
            f_content = f.read()
            for r_class in RELEVANT_CLASSES:
                if r_class in f_content:
                    if r_class in class_counts:
                        class_counts[r_class] += 1
                    else:
                        class_counts[r_class] = 1

# Print summary
print("Done! Found the following class counts:", class_counts)
