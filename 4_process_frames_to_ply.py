import pyrealsense2 as rs
import numpy as np
import open3d as o3d
import os
import json

# Function to find the closest transformation matrix based on EPOCH time
def find_closest_transformation(epoch_time, transformations):
    closest_time = min(transformations.keys(), key=lambda k: abs(k - epoch_time))
    return transformations[closest_time]

# User inputs for file paths
depth_folder = input("Enter the path to the folder containing depth frames: ")
color_folder = input("Enter the path to the folder containing color frames: ")
transformation_csv = input("Enter the path to the CSV file containing transformation matrices: ")
intrinsic_json_path = input("Enter the path to the intrinsic.json file: ")
output_point_cloud_path = input("Enter the path where you would like to save the combined point cloud: ")

# Load transformation matrices from CSV file using numpy
transformations_data = np.genfromtxt(transformation_csv, delimiter=',', skip_header=1)
transformations = {}
for row in transformations_data:
    epoch_time = int(row[0])
    matrix = row[1:].reshape(4, 4)
    transformations[epoch_time] = matrix

# Load camera intrinsics from JSON file
with open(intrinsic_json_path, 'r') as f:
    intrinsics_data = json.load(f)

pinhole_camera_intrinsic = o3d.camera.PinholeCameraIntrinsic(
    width=intrinsics_data['width'],
    height=intrinsics_data['height'],
    fx=intrinsics_data['intrinsic_matrix'][0],
    fy=intrinsics_data['intrinsic_matrix'][4],
    cx=intrinsics_data['intrinsic_matrix'][6],
    cy=intrinsics_data['intrinsic_matrix'][7]
)

# Process each frame pair
all_transformed_points_list = []

for filename in os.listdir(depth_folder):
    if filename.endswith(".png"):
        # Extract EPOCH time from filename
        epoch_time = int(os.path.splitext(filename)[0])

        # Load depth and color images
        depth_image_path = os.path.join(depth_folder, filename)
        color_image_path = os.path.join(color_folder, f"{epoch_time}.jpg")

        if not os.path.exists(color_image_path):
            continue

        depth_image_o3d = o3d.io.read_image(depth_image_path)
        color_image_o3d = o3d.io.read_image(color_image_path)

        rgbd_image_o3d = o3d.geometry.RGBDImage.create_from_color_and_depth(
            color=color_image_o3d,
            depth=depth_image_o3d,
            convert_rgb_to_intensity=False,
            depth_scale=1.0,
            depth_trunc=1000.0,
            stride=1
        )

        # Create point cloud from RGBD image
        pcd = o3d.geometry.PointCloud.create_from_rgbd_image(
            rgbd_image_o3d,
            pinhole_camera_intrinsic
        )

        # Find the closest transformation matrix based on EPOCH time
        transformation_matrix = find_closest_transformation(epoch_time, transformations)

        # Apply transformation matrix to point cloud
        pcd.transform(transformation_matrix)

        # Accumulate transformed points
        all_transformed_points_list.append(pcd)

# Combine all transformed point clouds into one point cloud for visualization or further processing
if all_transformed_points_list:
    combined_pcd = all_transformed_points_list[0]
    for pcd in all_transformed_points_list[1:]:
        combined_pcd += pcd

    # Optional: visualize the combined point cloud using Open3D's visualization tools
    o3d.visualization.draw_geometries([combined_pcd])

# Save combined point cloud to a file (optional)
o3d.io.write_point_cloud(output_point_cloud_path, combined_pcd)