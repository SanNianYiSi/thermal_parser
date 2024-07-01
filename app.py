import numpy as np
from thermal_parser import *

# Initialize the Thermal object
thermal = Thermal(dtype=np.float32)

# Parse the image to get the temperature array
temperature = thermal.parse(filepath_image='datasets/ZH20T/DJI_20240430104041_0001_T.JPG')

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
