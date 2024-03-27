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

import unittest
import _thread

import numpy as np

from thermal_parser.thermal import *


class TestThermal(unittest.TestCase):

    @staticmethod
    def get_multi_thread_test_func():
        def multi_thread_test_func(thermal: Thermal, filepath_image: str):
            for _ in range(5):
                temperature = thermal.parse_dirp2(filepath_image=filepath_image)
                assert isinstance(temperature, np.ndarray)

        return multi_thread_test_func

    def test_init(self):
        thermal = Thermal()
        assert thermal is not None

    def test_parse(self):
        thermal = Thermal()
        for filepath_image in [
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

            'images/H20N/DJI_0001_R.JPG',
            'images/M3T/DJI_0001_R.JPG',
            'images/M30T/DJI_0001_R.JPG',
        ]:
            temperature = thermal.parse(filepath_image=filepath_image)
            assert isinstance(temperature, np.ndarray)

    def test_parse_flir(self):
        thermal = Thermal()
        for filepath_image in [
            'images/FLIR.jpg',
            'images/FLIR_AX8.jpg',
            'images/FLIR_E40.jpg',
            'images/FLIR_T640.jpg',
        ]:
            temperature = thermal.parse_flir(filepath_image=filepath_image)
            assert isinstance(temperature, np.ndarray)

    def test_parse_dirp2(self):
        thermal = Thermal()
        for filepath_image in [
            'images/DJI_H20T.jpg',
            'images/DJI_XTS.jpg',
        ]:
            temperature = thermal.parse_dirp2(filepath_image=filepath_image)
            assert isinstance(temperature, np.ndarray)

    def test_parse_m2ea(self):
        thermal = Thermal()
        for filepath_image in [
            'images/M2EA/DJI_0001_R.JPG',
            'images/M2EA/DJI_0002_R.JPG',
            'images/M2EA/DJI_0003_R.JPG',
            'images/M2EA/DJI_0004_R.JPG',
            'images/M2EA/DJI_0005_R.JPG',

            'images/H20N/DJI_0001_R.JPG',
            'images/H20N/DJI_0002_R.JPG',
            'images/H20N/DJI_0003_R.JPG',
            'images/H20N/DJI_0004_R.JPG',

            'images/M3T/DJI_0001_R.JPG',

            'images/M30T/DJI_0001_R.JPG',
            'images/M30T/DJI_0002_R.JPG',
            'images/M30T/DJI_0003_R.JPG',
            'images/M30T/DJI_0004_R.JPG',
            'images/M30T/DJI_0005_R.JPG',
            'images/M30T/DJI_0015_R.JPG',
        ]:
            temperature = thermal.parse_dirp2(filepath_image=filepath_image, m2ea_mode=True)
            assert isinstance(temperature, np.ndarray)

    def test_multi_thread(self):
        thermal = Thermal()
        filepath_image = 'images/DJI_H20T.jpg'
        for _ in range(5):
            _thread.start_new_thread(TestThermal.get_multi_thread_test_func(), (thermal, filepath_image))

    def test_result(self):
        thermal = Thermal()
        filepath_image = 'images/DJI_H20T.jpg'
        temperature = thermal.parse_dirp2(filepath_image=filepath_image)
        assert 12 < np.min(temperature) < 14, 'temperature min:{}'.format(np.min(temperature))
        assert 27 < np.max(temperature) < 29, 'temperature max:{}'.format(np.max(temperature))


if __name__ == '__main__':
    unittest.main()
