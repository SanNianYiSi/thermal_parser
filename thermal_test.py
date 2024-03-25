"""
MIT License

Copyright (c) 2021 SanNianYiSi

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.
"""

import sys
import unittest
import _thread

import numpy as np

from thermal import *


class TestThermal(unittest.TestCase):

    @staticmethod
    def get_thermal() -> Thermal:
        dji_sdk_version = 'dji_thermal_sdk_v1.4_20220929'
        if 'win' in sys.platform:
            dirp_filename = f'plugins/{dji_sdk_version}/windows/release_x64/libdirp.dll'
            dirp_sub_filename = f'plugins/{dji_sdk_version}/windows/release_x64/libv_dirp.dll'
            iirp_filename = f'plugins/{dji_sdk_version}/windows/release_x64/libv_iirp.dll'
        else:
            dirp_filename = f'plugins/{dji_sdk_version}/linux/release_x64/libdirp.so'
            dirp_sub_filename = f'plugins/{dji_sdk_version}/linux/release_x64/libv_dirp.so'
            iirp_filename = f'plugins/{dji_sdk_version}/linux/release_x64/libv_iirp.so'
        if 'win' in sys.platform:
            exif_filename = 'plugins/exiftool-12.35.exe'
        else:
            exif_filename = None
        thermal = Thermal(
            dirp_filename=dirp_filename,
            dirp_sub_filename=dirp_sub_filename,
            iirp_filename=iirp_filename,
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
            'images/M2EA/DJI_0001_R.JPG',
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

    def test_parse_m2ea(self):
        thermal = TestThermal.get_thermal()
        for image_filename in [
            'images/M2EA/DJI_0001_R.JPG',
            'images/M2EA/DJI_0002_R.JPG',
            'images/M2EA/DJI_0003_R.JPG',
            'images/M2EA/DJI_0004_R.JPG',
            'images/M2EA/DJI_0005_R.JPG',

            'images/H20N/DJI_0001_R.JPG',
            'images/M3T/DJI_0001_R.JPG',
            'images/M30T/DJI_0001_R.JPG',
        ]:
            temperature = thermal.parse_dirp2(image_filename=image_filename, m2ea_mode=True)
            assert isinstance(temperature, np.ndarray)

    def test_multi_thread(self):
        thermal = TestThermal.get_thermal()
        image_filename = 'images/DJI_H20T.jpg'
        for _ in range(5):
            _thread.start_new_thread(TestThermal.get_multi_thread_test_func(), (thermal, image_filename))

    def test_result(self):
        thermal = TestThermal.get_thermal()
        image_filename = 'images/DJI_H20T.jpg'
        temperature = thermal.parse_dirp2(image_filename=image_filename)
        assert 12 < np.min(temperature) < 14, 'temperature min:{}'.format(np.min(temperature))
        assert 27 < np.max(temperature) < 29, 'temperature max:{}'.format(np.max(temperature))


if __name__ == '__main__':
    unittest.main()
