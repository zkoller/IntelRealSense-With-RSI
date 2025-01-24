# This is originally Steven Williams' code, but I modified the timestamp line for a different format

import socket
import csv
import os
import xml.etree.ElementTree as ET
from datetime import datetime
import time

def receive_data():
    # Get the user's desktop path and create the "Experiment Data" folder
    desktop = os.path.join(os.path.expanduser("~"), "Desktop")
    save_dir = os.path.join(desktop, "Experiment Data")
    os.makedirs(save_dir, exist_ok=True)  # Create the folder if it doesn't exist

    # Path to the CSV file
    csv_file_path = os.path.join(save_dir, "robot_data.csv")

    # IP and port of your computer where you want to receive data
    IP = "192.168.1.25"  # Change to your computer's IP address
    #IP = "0.0.0.0"
    PORT = 59152         # Port number used for communication (Check the KUKA setup)

    # Create a UDP socket
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        # Bind the socket to the address and port
        s.bind((IP, PORT))
        print(f"Listening on {IP}:{PORT}")

        # Open the CSV file for writing
        with open(csv_file_path, "w", newline="") as csvfile:
            # Define the CSV writer
            fieldnames = ['Timestamp', 'X_RIst', 'Y_RIst', 'Z_RIst', 'A_RIst', 'B_RIst', 'C_RIst',
                          'X_RSol', 'Y_RSol', 'Z_RSol', 'A_RSol', 'B_RSol', 'C_RSol',
                          'Delay', 'WeldVolt', 'WeldAmps', 'MotorAmps', 'WFS', 'IPOC', 'ErrorNum',
                          'C11', 'C12', 'C13', 'C14', 'C15', 'C16', 'C17', 'C18', 'C19', 'C110',
                          'i1', 'i2', 'i3', 'i4']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            # Write the header row to the CSV file
            writer.writeheader()

            while True:
                # Receive data from the robot (adjust buffer size if necessary)
                data, addr = s.recvfrom(1024)
                data_str = data.decode('utf-8')
                print(f"Received data from {addr}: {data_str}")

                # Get the current timestamp
                timestamp = int(time.time() * 1000)

                # Parse the XML message
                try:
                    root = ET.fromstring(data_str)

                    # Extract the relevant fields from the XML
                    RIst = root.find('RIst')
                    RSol = root.find('RSol')
                    Delay = root.find('Delay')
                    WeldVolt = root.find('WeldVolt').text
                    WeldAmps = root.find('WeldAmps').text
                    MotorAmps = root.find('MotorAmps').text
                    WFS = root.find('WFS').text
                    IPOC = root.find('IPOC').text
                    ErrorNum = root.find('ErrorNum').text
                    
                    # Extract the Tech data (C11 to C110)
                    Tech = root.find('Tech')
                    C11 = Tech.attrib.get('C11', '0.0')
                    C12 = Tech.attrib.get('C12', '0.0')
                    C13 = Tech.attrib.get('C13', '0.0')
                    C14 = Tech.attrib.get('C14', '0.0')
                    C15 = Tech.attrib.get('C15', '0.0')
                    C16 = Tech.attrib.get('C16', '0.0')
                    C17 = Tech.attrib.get('C17', '0.0')
                    C18 = Tech.attrib.get('C18', '0.0')
                    C19 = Tech.attrib.get('C19', '0.0')
                    C110 = Tech.attrib.get('C110', '0.0')

                    # Extract the Status data (i1 to i4)
                    Status = root.find('Status')
                    i1 = Status.attrib.get('i1', '0')
                    i2 = Status.attrib.get('i2', '0')
                    i3 = Status.attrib.get('i3', '0')
                    i4 = Status.attrib.get('i4', '0')

                    # Prepare data for writing into the CSV file
                    row = {
                        'Timestamp': timestamp,
                        'X_RIst': RIst.attrib['X'],
                        'Y_RIst': RIst.attrib['Y'],
                        'Z_RIst': RIst.attrib['Z'],
                        'A_RIst': RIst.attrib['A'],
                        'B_RIst': RIst.attrib['B'],
                        'C_RIst': RIst.attrib['C'],
                        'X_RSol': RSol.attrib['X'],
                        'Y_RSol': RSol.attrib['Y'],
                        'Z_RSol': RSol.attrib['Z'],
                        'A_RSol': RSol.attrib['A'],
                        'B_RSol': RSol.attrib['B'],
                        'C_RSol': RSol.attrib['C'],
                        'Delay': Delay.attrib['D'],
                        'WeldVolt': WeldVolt,
                        'WeldAmps': WeldAmps,
                        'MotorAmps': MotorAmps,
                        'WFS': WFS,
                        'IPOC': IPOC,
                        'ErrorNum': ErrorNum,
                        'C11': C11, 'C12': C12, 'C13': C13, 'C14': C14, 'C15': C15,
                        'C16': C16, 'C17': C17, 'C18': C18, 'C19': C19, 'C110': C110,
                        'i1': i1, 'i2': i2, 'i3': i3, 'i4': i4
                    }

                    # Write the data as a row in the CSV file
                    writer.writerow(row)

                except ET.ParseError as e:
                    print(f"Failed to parse XML: {e}")
                    continue

if __name__ == "__main__":
    receive_data()
