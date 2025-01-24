# The purpose of this file is to be able to record and save aligned realsense color and depth images.
# This is the same structure of a realsense_recorder.py provided by Open3d/pyrealsense2, although this version uses prompted inputs
# instead of required input arguments and also incorporates the realsense_helper.py file from Open3D so it is not 
# separately needed. There is also some additional functionality to preconfigure the specific recording parameters you
#  want to record in. 

# You press esc with the playback window active to end recording

# Heading from Open3d provided realsense_recorder.py:
# ----------------------------------------------------------------------------
# -                        Open3D: www.open3d.org                            -
# ----------------------------------------------------------------------------
# Copyright (c) 2018-2024 www.open3d.org
# SPDX-License-Identifier: MIT
# ----------------------------------------------------------------------------

# examples/python/reconstruction_system/sensors/realsense_recorder.py

# pyrealsense2 is required.
# Please see instructions in https://github.com/IntelRealSense/librealsense/tree/master/wrappers/python

import pyrealsense2 as rs
import numpy as np
import cv2
from os import makedirs
from os.path import exists, join, abspath
import shutil
import json
from enum import IntEnum
import time

class Preset(IntEnum):
    Custom = 0
    Default = 1
    Hand = 2
    HighAccuracy = 3
    HighDensity = 4
    MediumDensity = 5

def make_clean_folder(path_folder):
    if not exists(path_folder):
        makedirs(path_folder)
    else:
        user_input = input(f"{path_folder} not empty. Overwrite? (y/n) : ")
        if user_input.lower() == 'y':
            shutil.rmtree(path_folder)
            makedirs(path_folder)
        else:
            exit()

def save_intrinsic_as_json(filename, frame, profile, depth_scale, fps, stream_length_usec):
    intrinsics = frame.profile.as_video_stream_profile().intrinsics
    device_name = profile.get_device().get_info(rs.camera_info.name)
    serial_number = profile.get_device().get_info(rs.camera_info.serial_number)

    data = {
        "color_format": "RGB8",
        "depth_format": "Z16",
        "depth_scale": depth_scale,
        "device_name": device_name,
        "fps": fps,
        "height": intrinsics.height,
        "intrinsic_matrix": [
            intrinsics.fx, 0.0, 0.0,
            0.0, intrinsics.fy, 0.0,
            intrinsics.ppx, intrinsics.ppy, 1.0
        ],
        "serial_number": serial_number,
        "stream_length_usec": stream_length_usec,
        "width": intrinsics.width
    }

    with open(filename, 'w') as outfile:
        json.dump(data, outfile, indent=4)

def get_profiles():
    ctx = rs.context()
    devices = ctx.query_devices()

    color_profiles = []
    depth_profiles = []
    for device in devices:
        name = device.get_info(rs.camera_info.name)
        serial = device.get_info(rs.camera_info.serial_number)
        print('Sensor: {}, {}'.format(name, serial))
        print('Supported video formats:')
        for sensor in device.query_sensors():
            for stream_profile in sensor.get_stream_profiles():
                stream_type = str(stream_profile.stream_type())

                if stream_type in ['stream.color', 'stream.depth']:
                    v_profile = stream_profile.as_video_stream_profile()
                    fmt = stream_profile.format()
                    w, h = v_profile.width(), v_profile.height()
                    fps = v_profile.fps()

                    video_type = stream_type.split('.')[-1]
                    print('  {}: width={}, height={}, fps={}, fmt={}'.format(
                        video_type, w, h, fps, fmt))
                    if video_type == 'color':
                        color_profiles.append((w, h, fps, fmt))
                    else:
                        depth_profiles.append((w, h, fps, fmt))

    return color_profiles, depth_profiles

if __name__ == "__main__":
    # Display connected RealSense cameras and available streams/profiles
    color_profiles, depth_profiles = get_profiles()

    print('Referencing the above options, enter the appropriate values:')
    w = int(input("Image Width (default: 640): ") or 640)
    h = int(input("Image Height (default: 480): ") or 480)
    fps = int(input("Frames Per Second (default: 30): ") or 30)
    use_auto_exposure = input("Use auto exposure? (y/n) (default: y): ").lower() or 'y'
    output_folder = input("Enter the output folder path (default: friendly_recorder/): ") or 'friendly_recorder/'
    # The ".." means from this current running directory

    path_output = output_folder
    path_depth = join(output_folder, "depth")
    path_color = join(output_folder, "color")
    
    make_clean_folder(path_output)
    make_clean_folder(path_depth)
    make_clean_folder(path_color)

    # Create a pipeline
    pipeline = rs.pipeline()

    # Create a config and configure the pipeline to stream different resolutions of color and depth streams
    config = rs.config()

    config.enable_stream(rs.stream.depth, w, h, rs.format.z16, fps)
    config.enable_stream(rs.stream.color, w, h, rs.format.bgr8, fps)

    # Start streaming
    profile = pipeline.start(config)
    depth_sensor = profile.get_device().first_depth_sensor()

    if use_auto_exposure == 'y':
        depth_sensor.set_option(rs.option.enable_auto_exposure, True)
        print("Auto exposure enabled.")
    else:
        depth_sensor.set_option(rs.option.enable_auto_exposure, False)
        print("Auto exposure disabled.")

    # Select preset for recording based on user input
    preset_options = {preset.name: preset.value for preset in Preset}
    
    print("Available presets:")
    
    for name in preset_options.keys():
        print(name)
        
    selected_preset_name = input("Select a preset from the above options (default: Default): ") or "Default"
    
    selected_preset_value = preset_options.get(selected_preset_name.capitalize(), Preset.HighAccuracy)
    
    # Using selected preset for recording
    depth_sensor.set_option(rs.option.visual_preset, selected_preset_value)

    # Getting the depth sensor's depth scale (see rs-align example for explanation)
    depth_scale = depth_sensor.get_depth_scale()

    # We will not display the background of objects more than clipping_distance_in_meters meters away
    clipping_distance_in_meters = float(input("Enter maximum clipping distance in meters (default: 0.500): ") or 0.500)
    clipping_distance = clipping_distance_in_meters / depth_scale

    # We will not display the background of objects less than the min_distance_in_meters meters away
    min_distance_in_meters= float(input("Enter minimum clipping distance in meters (default: 0.070): ") or 0.070)
    min_distance = min_distance_in_meters / depth_scale

    # Create an align object
    align_to = rs.stream.color
    
    align = rs.align(align_to)

    # Streaming loop
    frame_count = 0
    
    start_time=time.time()
    try:
        while True:
            # Get frameset of color and depth
            frames = pipeline.wait_for_frames()

            # Align the depth frame to color frame
            aligned_frames = align.process(frames)

            # Get aligned frames
            aligned_depth_frame = aligned_frames.get_depth_frame()
            
            color_frame = aligned_frames.get_color_frame()

            # Validate that both frames are valid
            if not aligned_depth_frame or not color_frame:
                continue

            depth_image = np.asanyarray(aligned_depth_frame.get_data())
            
            color_image = np.asanyarray(color_frame.get_data())

            # Get frame timestamp and format it as a string suitable for filenames
            timestamp_ms=int(aligned_depth_frame.get_timestamp())
            timestamp_str=f"{timestamp_ms}"
            timestamp_domain_str=f"{aligned_depth_frame.get_frame_timestamp_domain()}"
            
            cv2.imwrite(f"{path_depth}/{timestamp_str}.png", depth_image)
            cv2.imwrite(f"{path_color}/{timestamp_str}.jpg", color_image)
            
            print(f"Saved color + depth image {frame_count:06d}")
                
            frame_count += 1

            # Remove background - Set pixels further than clipping_distance to grey
            
            grey_color = 153
            
            # Depth image is 1 channel; color is 3 channels
            
            depth_image_3d = np.dstack((depth_image, depth_image, depth_image))
            
            bg_removed=np.where((depth_image_3d > clipping_distance )| (depth_image_3d < min_distance),grey_color ,color_image) 

            # Render images
            
            depth_colormap = cv2.applyColorMap(cv2.convertScaleAbs(depth_image, alpha=0.09), cv2.COLORMAP_JET)
            
            images = np.hstack((bg_removed, depth_colormap))
            
            cv2.namedWindow('Recorder Realsense D405', cv2.WINDOW_AUTOSIZE)
            
            cv2.imshow('Recorder Realsense D405', images)
            
            key = cv2.waitKey(1)

            # If 'esc' button pressed, escape loop and exit program
            
            if key == 27:
                cv2.destroyAllWindows()
                break
                
    finally:
         pipeline.stop()
         end_time=time.time()
         stream_length_usec=int((end_time-start_time)*1000000)
         #save_intrinsic_as_json(filename, frame, profile, depth_scale, fps, stream_length_usec)
         save_intrinsic_as_json(join(output_folder,"camera_intrinsic.json"),color_frame ,profile ,depth_scale ,fps ,stream_length_usec)
         print('Intrinsics saved and the timestamps saved in the following domain:'+timestamp_domain_str)