import sys
import unittest

import numpy as np

from thermal import *


class TestThermal(unittest.TestCase):

    def test_init(self):
        if 'win' in sys.platform:
            dji_sdk_filename = ''
        else:
            dji_sdk_filename = ''
        if 'win' in sys.platform:
            exif_filename = ''
        else:
            exif_filename = None
        thermal = Thermal(
            dji_sdk_filename=dji_sdk_filename,
            exif_filename=exif_filename,
        )
        assert thermal is not None

    def test_parser(self):
        dji_sdk_filename = ''
        exif_filename = ''
        image_filename = ''
        thermal = Thermal(
            dji_sdk_filename=dji_sdk_filename,
            exif_filename=exif_filename,
        )
        temperature = thermal(
            image_filename=image_filename,
        )
        assert isinstance(temperature, np.ndarray)

    def test_parse_flir(self):
        pass

    def test_parse_dirp2(self):
        dji_sdk_filename = ''
        exif_filename = ''
        image_filename = ''
        thermal = Thermal(
            dji_sdk_filename=dji_sdk_filename,
            exif_filename=exif_filename,
        )
        temperature = thermal.parse_dirp2(
            image_filename=image_filename,
        )
        assert isinstance(temperature, np.ndarray)

    def test_parse_dirp3(self):
        pass

    def test_multi_thread(self):
        pass

    def test_multi_process(self):
        pass


if __name__ == '__main__':
    unittest.main()
