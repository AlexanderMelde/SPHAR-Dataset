"""
Collection of functions useful for cutting and cropping dataset videos

Author: Alexander Melde (alexander@melde.net)
"""

import os
import shlex
import subprocess

import cv2
import numpy as np


def print_if(bool_var, *args):
    """ shortcut to print only if bool_var=True

    Args:
        bool_var (bool): whether or not to print
        *args: all additional args will be passed to print()
    """
    if bool_var:
        return print(*args)


def cut_and_crop(mode, input_video_cap, input_fps, input_size, input_video_name, dataset_name,
                 activity_name, activity_id, output_dir, timespan, bbox,
                 preview_video=False, crop=True, verbose_output=False):
    """Cut and Crops Video to a specific Action Instance, requires input video to be already read
       outside the function, as this function is often called inside some loop, 
       so this saves computation time.

    Args:
        mode (string): either "cv2" or "ffmpeg"
        input_video_cap (VideoCapture): reference to input video,
                                        as returned by cv2.VideoCapture(input_video)
        input_fps (int): input video fps, as returned by int(cap.get(cv2.CAP_PROP_FPS))
        input_size (tuple(int,int)): size of the input video (w,h),
                                     tip: use cap.get(cv2.CAP_PROP_FRAME_WIDTH)
        input_video_name (string): name of the input video, used in output video name
        dataset_name (string): name of the dataset, used in output video name
        activity_name (string): name of the activity, used in output video name and output folder
        activity_id (int): unique id or incremental counter of the activity,
                           used in output video name
        output_dir (string): path to the video directory (not activity-specific)
        timespan (tuple(int,int)): start and end frame number to cut
        bbox ({'x': int, 'y':int, 'w':int, 'h':int}): bounding box to crop to, consisting of
                                                      left top coordinates for x and y and the
                                                      width and heigth and of the action
        preview_video (bool, optional): Set to True to show a preview window of the video.
                                        Defaults to False.
        crop (bool, optional): Set to False to just cut without cropping. Defaults to True.
        verbose_output (bool, optional): Set to True to output additional debugging information.
                                         Defaults to False.

    Returns:
        bool: True if cutting was sucessfull
    """
    video_name_out = f"{dataset_name}_{input_video_name}_{activity_name}_{activity_id}.mp4"
    output_dir = os.path.join(output_dir, activity_name)

    # init video writing
    os.makedirs(output_dir, exist_ok=True)

    outfile = os.path.join(output_dir, video_name_out)
    if os.path.isfile(outfile):
        print_if(verbose_output, "skipping file, already exists:", outfile)
        return False

    ctu_val = 64  # ffmpeg h265 CTU

    #  calculate output video size
    size = (bbox['w'], bbox['h']) if crop else input_size
    # ffmpeg throws an error when having odd dimensions that are not dividable by 2,
    # so i just add a pixel to the size and stretch the original image by 1 pixel later.
    size_e = (size[0]+1 if size[0] % 2 != 0 else size[0],
              size[1]+1 if size[1] % 2 != 0 else size[1])
    if (np.array(size_e) < (ctu_val, ctu_val)).any():
        print_if(verbose_output, "SMALLER THAN CTU!===Resizing to CTUxCTU square")
        size_e = (ctu_val, ctu_val)
    print_if(verbose_output, "size", size, size_e)
    if mode == "cv2":
        out = cv2.VideoWriter(
            outfile, cv2.VideoWriter_fourcc(*'mp4v'), input_fps, size_e)
    elif mode == "ffmpeg":
        # generate and run ffmpeg command
        verb_flags = ' -hide_banner -loglevel error' if not verbose_output else ''
        verb_x265 = 'log-level=error:' if not verbose_output else ''

        ffmpeg_cmd = (f'/usr/bin/ffmpeg -y -s {size_e[0]}x{size_e[1]} -pixel_format'
                      + f' bgr24 -f rawvideo -r {input_fps} -i pipe: -vcodec libx265'
                      + f' -pix_fmt yuv420p -crf 24{verb_flags}'
                      + f' -x265-params "{verb_x265}ctu={ctu_val}" "{outfile}"')

        print_if(verbose_output, "now cutting to", outfile, "using cmd", ffmpeg_cmd)

        process = subprocess.Popen(shlex.split(
            ffmpeg_cmd), stdin=subprocess.PIPE)

    # seek to the beginning of the cutting timespan and loop through frames of input video
    input_video_cap.set(cv2.CAP_PROP_POS_FRAMES, timespan[0])
    frame_returned = True
    while input_video_cap.isOpened() and frame_returned and (mode != "cv2" or out.isOpened()):
        frame_returned, frame = input_video_cap.read()
        frame_number = input_video_cap.get(cv2.CAP_PROP_POS_FRAMES) - 1

        # check if timespan end is not reached yet
        if frame_number < timespan[1] and frame is not None:
            if crop:
                # crop to relevant image area
                frame_cropped = frame[bbox['y']:bbox['y']+bbox['h'],
                                      bbox['x']:bbox['x']+bbox['w']]

                if size != size_e:
                    # resize to even frame size if needed:
                    frame_cropped = cv2.resize(frame_cropped,
                                               (size_e[0], size_e[1]))

            if preview_video:
                # Show processed image using opencv
                cv2.imshow('Frame', frame_cropped if crop else frame)

            if mode == "cv2":
                out.write(frame_cropped if crop else frame)
            elif mode == "ffmpeg":
                # Write cropped or raw video frame to input stream of ffmpeg sub-process.
                process.stdin.write(
                    (frame_cropped if crop else frame).tobytes())
        else:
            break

        # Press Q on keyboard to exit earlier
        if preview_video and (cv2.waitKey(25) & 0xFF == ord('q')):
            break

    if mode == "cv2":
        out.release()
    elif mode == "ffmpeg":
        process.stdin.close()  # Close and flush stdin
        process.wait()         # Wait for sub-process to finish
        process.terminate()    # Terminate the sub-process

    return True
