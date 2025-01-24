import csv
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from datetime import datetime
from tqdm import tqdm
from scipy.spatial.transform import Rotation as R
import tkinter as tk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# Function to read CSV file and parse transformation matrices and timestamps
def read_csv(file_path):
    timestamps = []
    matrices = []
    with open(file_path, 'r') as file:
        reader = csv.reader(file)
        for row in reader:
            timestamp = int(row[0])
            matrix = np.array(row[1:], dtype=float).reshape(4, 4)
            timestamps.append(timestamp)
            matrices.append(matrix)
    return timestamps, matrices

# Function to apply transformation matrix to a vector
def transform_vector(matrix, vector):
    rotation_matrix = matrix[:3, :3]  # Extract rotation part
    translation_vector = matrix[:3, 3]  # Extract translation part
    transformed_vector = rotation_matrix @ vector + translation_vector
    return transformed_vector

# Function to calculate XYZABC values from a transformation matrix
def calculate_xyzabc(matrix):
    translation = matrix[:3, 3]
    rotation_matrix = matrix[:3, :3]
    r = R.from_matrix(rotation_matrix)
    euler_angles = r.as_euler('xyz', degrees=True)
    return np.concatenate((translation, euler_angles))

# Function to update the plot for each frame of the animation
def update(frame):
    ax.cla()  # Clear the previous frame
    
    # Apply the transformation matrix to get new root and direction (relative to initial position)
    transformed_vector = transform_vector(matrices[frame], initial_vector)
    
    # Calculate XYZABC values and format them to 3 decimal places
    xyzabc_values = calculate_xyzabc(matrices[frame])
    xyzabc_formatted = np.round(xyzabc_values, 3)
    
    # Plot the original and transformed vectors
    ax.quiver(0, 0, 0, initial_vector[0], initial_vector[1], initial_vector[2], color='blue', label='Initial Vector')
    
    # Plot the transformed vector starting from its translation position
    ax.quiver(xyzabc_values[0], xyzabc_values[1], xyzabc_values[2],
              transformed_vector[0] - xyzabc_values[0],
              transformed_vector[1] - xyzabc_values[1],
              transformed_vector[2] - xyzabc_values[2],
              color='red', label='Transformed Vector')
    
    # Update the timestamp and frame count display
    timestamp_str = datetime.fromtimestamp(timestamps[frame] / 1000).strftime('%Y-%m-%d %H:%M:%S')
    text_time.set_text(f'Time: {timestamp_str} (EPOCH: {timestamps[frame]})\nFrame: {frame + 1}/{len(timestamps)}\nXYZABC: {xyzabc_formatted}')
    
    # Set static axis limits
    ax.set_xlim(-max_extent * 1.5, max_extent * 1.5)
    ax.set_ylim(-max_extent * 1.5, max_extent * 1.5)
    ax.set_zlim(-max_extent * 1.5, max_extent * 1.5)

# Function to create and save the animation
def create_animation():
    global timestamps, matrices, fig, ax, text_time, initial_vector, max_extent
    
    timestamps, matrices = read_csv(csv_file_path)
    
    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')
    
    scaling_factor = 500.0  # Increase this value to scale up the vector magnitude
    initial_vector = np.array([1, 0, 0]) * scaling_factor  # Initial vector along x-axis
    
    text_time = plt.figtext(0.02, 0.9, '', fontsize=10)
    
    # Calculate axis limits based on translations in matrices
    translations = [matrix[:3, 3] for matrix in matrices]
    global max_extent 
    max_extent = np.max(np.abs(translations))

def start_animation():
    global ani_running
    ani_running = True
    ani.event_source.start()

def stop_animation():
    global ani_running
    ani_running = False
    ani.event_source.stop()

def update_frame(val):
    global current_frame
    
    current_frame = int(val)

def on_slider_change(val):
   update_frame(val)
   update(current_frame)
   canvas.draw_idle()  # Redraw canvas after updating frame

# Main function to create the GUI and run the animation
if __name__ == "__main__":
    
   csv_file_path ='transformations.csv'
   output_file_path ='animation.gif' 
   
   create_animation()
   
   root=tk.Tk()
   root.title("Animation GUI")
   
   canvas=FigureCanvasTkAgg(fig, master=root) 
   canvas.draw()
   canvas.get_tk_widget().pack(side=tk.TOP,
                                fill=tk.BOTH,
                                expand=1)
   
   toolbar_frame=tk.Frame(root)
   toolbar_frame.pack(side=tk.BOTTOM,
                      fill=tk.X)
   
   play_button=tk.Button(master=toolbar_frame,
                         text="Play",
                         command=start_animation)
   
   play_button.pack(side=tk.LEFT)
   
   pause_button=tk.Button(master=toolbar_frame,
                          text="Pause",
                          command=stop_animation)
   
   pause_button.pack(side=tk.LEFT)

   slider=tk.Scale(master=toolbar_frame,
                   from_=0,
                   to=len(timestamps)-1,
                   orient=tk.HORIZONTAL,
                   length=300,
                   command=on_slider_change)

   slider.pack(side=tk.LEFT)

   current_frame = 0
   
   ani_running = False
   
   def update_with_slider(frame):
       if not ani_running:
           return

       slider.set(frame)  # Update slider position based on current frame in animation

       update(frame)

       canvas.draw_idle()

   ani=FuncAnimation(fig,
                     update_with_slider,
                     frames=len(timestamps),
                     repeat=False)

root.mainloop()