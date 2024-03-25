# FLIR/DJI IR Camera Data Parser, Python Version

Parser infrared camera data as `NumPy` data.

## Usage

* Clone this respository and `cd thermal_parser`.
* Run `pip install -r requirements.txt` in the console
* If you run this project code on Linux, make sure [exiftool](https://exiftool.org/install.html) is installed first or run `sudo apt-get install libimage-exiftool-perl` in the console to install [exiftool](https://exiftool.org/install.html).
* Copy `thermal.py` file to project directory.
* Copy `plugins` folder to same directory.
* Try the following code:

**win 64**

```python
import numpy as np
from thermal import Thermal

thermal = Thermal(
    dirp_filename='plugins/dji_thermal_sdk_v1.1_20211029/windows/release_x64/libdirp.dll',
    dirp_sub_filename='plugins/dji_thermal_sdk_v1.1_20211029/windows/release_x64/libv_dirp.dll',
    iirp_filename='plugins/dji_thermal_sdk_v1.1_20211029/windows/release_x64/libv_iirp.dll',
    exif_filename='plugins/exiftool-12.35.exe',
    dtype=np.float32,
)
temperature = thermal.parse_dirp2(image_filename='images/DJI_H20T.jpg')
assert isinstance(temperature, np.ndarray)
```

**linux**

```python
import numpy as np
from thermal import Thermal

thermal = Thermal(
    dirp_filename='plugins/dji_thermal_sdk_v1.1_20211029/linux/release_x64/libdirp.so',
    dirp_sub_filename='plugins/dji_thermal_sdk_v1.1_20211029/linux/release_x64/libv_dirp.so',
    iirp_filename='plugins/dji_thermal_sdk_v1.1_20211029/linux/release_x64/libv_iirp.so',
    exif_filename=None,
    dtype=np.float32,
)
temperature = thermal.parse_dirp2(image_filename='images/DJI_H20T.jpg')
assert isinstance(temperature, np.ndarray)
```

## Supported IR Camera

* DJI H20T
* DJI XT2
* DJI XTR
* DJI XTS
* FLIR
* FLIR AX8
* FLIR B60
* FLIR E40
* FLIR T640

Set `m2ea_mode=True` when parsing the following image. 
* M2EA / MAVIC2-ENTERPRISE-ADVANCED / "御"2 行业进阶版
* DJI H20T
- DJI M3T
- DJI M30T

## References

* [DJI Thermal SDK](https://www.dji.com/cn/downloads/softwares/dji-thermal-sdk) The DJI Thermal SDK enables you to process R-JPEG (Radiometric JPEG) images which were captured by DJI infrared camera products.
* [Thermal Image Analysis](https://github.com/detecttechnologies/Thermal-Image-Analysis) A tool for analyzing and annotating thermal images.
* [Base codes for Thermography](https://github.com/detecttechnologies/thermal_base) A python package for decoding and common processing for thermographs / thermograms
* [thermography](https://github.com/cdeldon/thermography) This repository contains the implementation of a feasibility study for automatic detection of defected solar panel modules.
