import sys
import unittest
import _thread
import multiprocessing

import numpy as np

from thermal import *


class TestThermal(unittest.TestCase):

    @staticmethod
    def get_thermal() -> Thermal:
        if 'win' in sys.platform:
            dji_sdk_filename = 'plugins/dji_sdk/lib/windows/release_x64/libdirp.dll'
        else:
            dji_sdk_filename = 'plugins/dji_sdk/lib/linux/release_x64/libdirp.so'
        if 'win' in sys.platform:
            exif_filename = 'plugins/exiftool-12.35.exe'
        else:
            exif_filename = None
        thermal = Thermal(
            dji_sdk_filename=dji_sdk_filename,
            exif_filename=exif_filename,
        )
        return thermal

    @staticmethod
    def get_multi_thread_test_func():
        def multi_thread_test_func(thermal: Thermal, image_filename: str):
            for _ in range(5):
                temperature = thermal.parse_dirp2(image_filename=image_filename)
                assert isinstance(temperature, np.ndarray)

        return multi_thread_test_func

    def test_init(self):
        thermal = TestThermal.get_thermal()
        assert thermal is not None

    def test_parse(self):
        thermal = TestThermal.get_thermal()
        for image_filename in [
            'images/DJI_H20T.jpg',
            'images/DJI_XT2.jpg',
            'images/DJI_XTR.jpg',
            'images/DJI_XTS.jpg',
            'images/FLIR.jpg',
            'images/FLIR_AX8.jpg',
            'images/FLIR_B60.jpg',
            'images/FLIR_E40.jpg',
            'images/FLIR_T640.jpg',
        ]:
            temperature = thermal(image_filename=image_filename)
            assert isinstance(temperature, np.ndarray)

    def test_parse_flir(self):
        thermal = TestThermal.get_thermal()
        for image_filename in [
            'images/FLIR.jpg',
            'images/FLIR_AX8.jpg',
            'images/FLIR_E40.jpg',
            'images/FLIR_T640.jpg',
        ]:
            temperature = thermal.parse_flir(image_filename=image_filename)
            assert isinstance(temperature, np.ndarray)

    def test_parse_dirp2(self):
        thermal = TestThermal.get_thermal()
        for image_filename in [
            'images/DJI_H20T.jpg',
            'images/DJI_XTS.jpg',
        ]:
            temperature = thermal.parse_dirp2(image_filename=image_filename)
            assert isinstance(temperature, np.ndarray)

    def test_parse_dirp3(self):
        pass

    def test_multi_thread(self):
        thermal = TestThermal.get_thermal()
        image_filename = 'images/DJI_H20T.jpg'
        for _ in range(5):
            _thread.start_new_thread(TestThermal.get_multi_thread_test_func(), (thermal, image_filename))


if __name__ == '__main__':
    unittest.main()
