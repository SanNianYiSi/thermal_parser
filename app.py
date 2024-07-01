import numpy as np
from thermal_parser import *

thermal = Thermal(dtype=np.float32)
temperature = thermal.parse(filepath_image='datasets/ZH20T/DJI_20240430104041_0001_T.JPG')
print(temperature)
test = isinstance(temperature, np.ndarray)
print(test)
assert isinstance(temperature, np.ndarray)