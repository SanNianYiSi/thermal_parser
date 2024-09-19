import os
import numpy as np
from thermal_parser import *

# Initialize the Thermal object
thermal = Thermal(dtype=np.float32)

# Dataset dir
dataset = "H30T"
dir = os.path.join("images", dataset)

# Parse the image to get the temperature array
for image in os.listdir(dir):
    path_image = os.path.join(dir, image)
    print(f"Analysing image: {path_image}")
    temperature = thermal.parse(filepath_image=path_image)

    # Print the temperature array (optional, for debugging)
    print(temperature)

    # Check if the temperature is an instance of np.ndarray
    test = isinstance(temperature, np.ndarray)
    print(test)
    assert isinstance(temperature, np.ndarray)

    # Find and print the min and max temperatures
    min_temp = np.min(temperature)
    max_temp = np.max(temperature)

    print(f"Min temperature: {min_temp}")
    print(f"Max temperature: {max_temp}")
    print(f"Shape: {temperature.shape}")

    # Specify the pixel coordinates
    x = 640  # replace with your desired x-coordinate
    y = 0  # replace with your desired y-coordinate

    # Check if the coordinates are within the valid range
    if 0 <= y < 512 and 0 <= x < 640:
        # Get the temperature at the specified pixel
        pixel_temp = temperature[y, x]
        print(f"Temperature at pixel ({x}, {y}): {pixel_temp}")
    else:
        print(f"Pixel coordinates ({x}, {y}) are out of bounds.")
