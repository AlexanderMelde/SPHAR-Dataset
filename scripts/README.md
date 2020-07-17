# Scripts 
This folder contains all the scripts used to create **SPHAR**, the **S**urveillance **P**erspective **H**uman **A**ction **R**ecognition Dataset.

## Descriptions
### Video Conversion
- `convert_to_mp4.py` is a universal video converter based on `ffmpeg`. It can convert any video input format to a high efficiency video codec (HEVC) H265 .mp4 format.
- `rename_videos.py` is a simple batch-renaming tool that appends the original datasets name to each videos filename to preserve reference to the original dataset when aggregating videos to the 15 classes of SPHAR.
- `view_video.py` is a simple OpenCV based video viewer used to debug different video encodings, independent from other installed video-viewers like VLC or Ubuntu's default video player.

### Video Filtering
- `filter_meva.py` is a convienience script used to generate a list of paths to all videos that contain certain specific MEVA classes. The list can be used with `copy_filtered.py` to copy all files from the list to a specific folder. This was helpful for sorting out irrelevant videos before converting them, as this was a very time-intensive task.
- `count_meva.py` was similarly used to get a quick overview of the number of action occurences in the MEVA dataset.

### Spatiotemporal Cropping
- `cutcrop_functions.py` is a collection of functions useful for cutting and cropping dataset videos. It contains the `cut_and_crop()` function that is used by the other cropping scripts to cut and crop a video to a specific action instance. 
- `crop_okutama.py`, `crop_meva.py`, `crop_ucaerial.py` and `crop_virat.py` are dataset-specific scripts that parse the original annotation files (which are each formatted differently) to create a python object, which can be passed to the `cut_and_crop()` function (or just be converted to json for easier readability). 

### Temporal Cutting
- all spatiotemporal cropping tools can be used for temporal (time-only) cutting by setting the `ENABLE_CROP` variable `False`.
- `cut_meva.py` is a time-only cutting tool for the meva dataset. It will merge overlapping action instances from multiple persons and can be used to generate longer action videos from the whole scene (spatially uncropped).

## Installation
Requires Python 3.6 or newer and an up-to-date ffmpeg that shipped with the H.265 codec.
1) [Install ffmpeg](https://ffmpeg.org/download.html), e.g. using `sudo apt install ffmpeg`.
2) Download the repo using `git clone git@github.com:AlexanderMelde/SPHAR-Dataset.git`
3) Install Dependencies using `pip install -r 'SPHAR-Dataset/scripts/requirements.txt'`
