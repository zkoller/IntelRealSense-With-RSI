import numpy as np
import pandas as pd
import math
import os
from datetime import datetime

def euler_to_matrix(x, y, z, a, b, c):
    try:
        # Convert angles from degrees to radians
        a = math.radians(a)
        b = math.radians(b)
        c = math.radians(c)

        # Calculate rotation matrices for each axis
        Rx = np.array([[1, 0, 0],
                       [0, math.cos(a), -math.sin(a)],
                       [0, math.sin(a), math.cos(a)]])
        
        Ry = np.array([[math.cos(b), 0, math.sin(b)],
                       [0, 1, 0],
                       [-math.sin(b), 0, math.cos(b)]])
        
        Rz = np.array([[math.cos(c), -math.sin(c), 0],
                       [math.sin(c), math.cos(c), 0],
                       [0, 0, 1]])

        # Combined rotation matrix
        R = Rz @ Ry @ Rx

        # Create the transformation matrix
        T = np.eye(4)
        T[:3, :3] = R
        T[:3, 3] = [x, y, z]

        return T
    except Exception as e:
        print(f"Error in euler_to_matrix: {e}")
        return None
    
def convert_to_epoch(timestamp):
    try:
        # Try to convert directly if it's already in EPOCH time in ms
        epoch_time = int(timestamp)
    except ValueError:
        # If conversion fails, try parsing with and without milliseconds
        try:
            dt = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S.%f')
        except ValueError:
            dt = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
        epoch_time = int(dt.timestamp() * 1000)
    return epoch_time  

def process_csv(input_csv_path):
    if not os.path.exists(input_csv_path):
        print(f"Error: The file {input_csv_path} does not exist.")
        return
    
    try:
        # Read the CSV file
        df = pd.read_csv(input_csv_path)
    except Exception as e:
        print(f"Error reading CSV file: {e}")
        return

    # Check if required columns are present
    required_columns = ['Timestamp', 'X_RIst', 'Y_RIst', 'Z_RIst', 'A_RIst', 'B_RIst', 'C_RIst']
    if not all(column in df.columns for column in required_columns):
        print(f"Error: Input CSV must contain columns: {required_columns}")
        return

    # Prepare list to store transformation matrices with timestamps
    transformations = []

    try:
        # Get the initial transformation matrix (identity matrix)
        initial_row = df.iloc[0]
        initial_T = euler_to_matrix(initial_row['X_RIst'], initial_row['Y_RIst'], initial_row['Z_RIst'],
                                    initial_row['A_RIst'], initial_row['B_RIst'], initial_row['C_RIst'])
        
        if initial_T is None:
            print("Error: Failed to calculate the initial transformation matrix.")
            return
        
        for index, row in df.iterrows():
            timestamp_str = row['Timestamp']
            timestamp = convert_to_epoch(timestamp_str)
            x = row['X_RIst']
            y = row['Y_RIst']
            z = row['Z_RIst']
            a = row['A_RIst']
            b = row['B_RIst']
            c = row['C_RIst']

            # Calculate the transformation matrix relative to the initial position
            current_T = euler_to_matrix(x, y, z, a, b, c)
            
            if current_T is None:
                print(f"Error: Failed to calculate transformation matrix for row {index}.")
                continue
            
            relative_T = np.linalg.inv(initial_T) @ current_T
            
            # Append timestamp and flattened transformation matrix to the list of transformations
            transformations.append([timestamp] + relative_T.flatten().tolist())
        
    except Exception as e:
        print(f"Error processing CSV data: {e}")
        return

    try:
        # Save the transformation matrices with timestamps to a new CSV file
        output_csv_path = input("Enter the path where you would like to save the transformation matrices CSV: ")

        if os.path.exists(output_csv_path):
            overwrite = input(f"The file {output_csv_path} already exists. Do you want to overwrite it? (yes/no): ").strip().lower()
            if overwrite != 'yes':
                print("Operation cancelled by user.")
                return
        
        output_df = pd.DataFrame(transformations)
        
        output_df.to_csv(output_csv_path, index=False)
        
    except Exception as e:
        print(f"Error saving output CSV file: {e}")

if __name__ == "__main__":
    input_csv_path = input("Enter the path to the CSV file containing X,Y,Z,A,B,C data: ")
    process_csv(input_csv_path)