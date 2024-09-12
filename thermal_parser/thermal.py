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

import os
import re
import platform
import subprocess
import sys
from ctypes import *
from io import BufferedIOBase, BytesIO
from typing import BinaryIO, Dict, List, Optional, Tuple, Union

import numpy as np
from PIL import Image

__all__ = [
    'Thermal',
]

DIRP_HANDLE = c_void_p
DIRP_VERBOSE_LEVEL_NONE = 0  # 0: Print none
DIRP_VERBOSE_LEVEL_DEBUG = 1  # 1: Print debug log
DIRP_VERBOSE_LEVEL_DETAIL = 2  # 2: Print all log
DIRP_VERBOSE_LEVEL_NUM = 3  # 3: Total number


def get_default_filepaths() -> List[str]:
    folder_plugin = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'plugins')
    system = platform.system()
    sdk = "dji_thermal_sdk_v1.4_20220929"
    architecture = "x64" if platform.architecture()[0] == "64bit" else "x86"
    extension = "so" if system == "Linux" else "dll"
    exiftool = "exiftool" if system == "Linux" else f"{folder_plugin}/exiftool-12.35.exe"
    files = [
        f'{sdk}/{system.lower()}/release_{architecture}/libdirp.{extension}',
        f'{sdk}/{system.lower()}/release_{architecture}/libv_dirp.{extension}',
        f'{sdk}/{system.lower()}/release_{architecture}/libv_iirp.{extension}',
    ]
    if system not in ("Windows", "Linux") or architecture not in ("x64", "x86"):
        raise NotImplementedError(f'currently not supported for running on this platform: {system} {architecture}')
    
    return *[os.path.join(folder_plugin, v) for v in files], exiftool



class dirp_rjpeg_version_t(Structure):
    """
    References:
        * [DJI Thermal SDK](https://www.dji.com/cn/downloads/softwares/dji-thermal-sdk)
    """

    _fields_ = [
        # Version number of the opened R-JPEG itself.
        ('rjpeg', c_uint32),
        # Version number of the header data in R-JPEG
        ('header', c_uint32),
        # Version number of the curve LUT data in R-JPEG
        ('curve', c_uint32),
    ]


class dirp_resolotion_t(Structure):
    """
    References:
        * [DJI Thermal SDK](https://www.dji.com/cn/downloads/softwares/dji-thermal-sdk)
    """

    _fields_ = [
        # Horizontal size
        ('width', c_uint32),
        # Vertical size
        ('height', c_uint32),
    ]


class dirp_measurement_params_t(Structure):
    """
    References:
        * [DJI Thermal SDK](https://www.dji.com/cn/downloads/softwares/dji-thermal-sdk)
    """

    _fields_ = [
        # The distance to the target. Value range is [1~25] meters.
        ('distance', c_float),
        # How strongly the target surface is emitting energy as thermal radiation. Value range is [0.10~1.00].
        ('humidity', c_float),
        # The relative humidity of the environment. Value range is [20~100] percent. Defualt value is 70%.
        ('emissivity', c_float),
        # Reflected temperature in Celsius.
        # The surface of the target that is measured could reflect the energy radiated by the surrounding objects.
        # Value range is [-40.0~500.0]
        ('reflection', c_float),
    ]


# Constants
SEGMENT_SEP = b'\xff'
APP1_MARKER = b'\xe1'
MAGIC_FLIR_DEF = b'FLIR\x00'

CHUNK_APP1_BYTES_COUNT = len(APP1_MARKER)
CHUNK_LENGTH_BYTES_COUNT = 2
CHUNK_MAGIC_BYTES_COUNT = len(MAGIC_FLIR_DEF)
CHUNK_SKIP_BYTES_COUNT = 1
CHUNK_NUM_BYTES_COUNT = 1
CHUNK_TOT_BYTES_COUNT = 1
CHUNK_PARTIAL_METADATA_LENGTH = CHUNK_APP1_BYTES_COUNT + CHUNK_LENGTH_BYTES_COUNT + CHUNK_MAGIC_BYTES_COUNT
CHUNK_METADATA_LENGTH = (
    CHUNK_PARTIAL_METADATA_LENGTH + CHUNK_SKIP_BYTES_COUNT + CHUNK_NUM_BYTES_COUNT + CHUNK_TOT_BYTES_COUNT
)


def unpack(path_or_stream: Union[str, BinaryIO]) -> np.ndarray:
    """Unpacks the FLIR image, meaning that it will return the thermal data embedded in the image.

    Parameters
    ----------
    path_or_stream : Union[str, BinaryIO]
        Either a path (string) to a FLIR file, or a byte stream such as
        BytesIO or file opened as `open(file_path, 'rb')`.

    Returns
    -------
    FlyrThermogram
        When successful, a FlyrThermogram object containing thermogram data.
    """
    if isinstance(path_or_stream, str) and os.path.isfile(path_or_stream):
        with open(path_or_stream, 'rb') as flirh:
            return unpack(flirh)
    elif isinstance(path_or_stream, (BufferedIOBase, BinaryIO)):
        stream = path_or_stream
        flir_app1_stream = extract_flir_app1(stream)
        flir_records = parse_flir_app1(flir_app1_stream)
        raw_np = parse_thermal(flir_app1_stream, flir_records)

        return raw_np
    else:
        raise ValueError('Incorrect input')


def extract_flir_app1(stream: BinaryIO) -> BinaryIO:
    """Extracts the FLIR APP1 bytes.

    Parameters
    ---------
    stream : BinaryIO
        A full bytes stream of a JPEG file, expected to be a FLIR file.

    Raises
    ------
    ValueError
        When the file is invalid in one the next ways, a
        ValueError is thrown.

        * File is not a JPEG
        * A FLIR chunk number occurs more than once
        * The total chunks count is inconsistent over multiple chunks
        * No APP1 segments are successfully parsed

    Returns
    -------
    BinaryIO
        A bytes stream of the APP1 FLIR segments
    """
    # Check JPEG-ness
    _ = stream.read(2)

    chunks_count: Optional[int] = None
    chunks: Dict[int, bytes] = {}
    while True:
        b = stream.read(1)
        if b == b'':
            break

        if b != SEGMENT_SEP:
            continue

        parsed_chunk = parse_flir_chunk(stream, chunks_count)
        if not parsed_chunk:
            continue

        chunks_count, chunk_num, chunk = parsed_chunk
        chunk_exists = chunks.get(chunk_num, None) is not None
        if chunk_exists:
            raise ValueError('Invalid FLIR: duplicate chunk number')
        chunks[chunk_num] = chunk

        # Encountered all chunks, break out of loop to process found metadata
        if chunk_num == chunks_count:
            break

    if chunks_count is None:
        raise ValueError('Invalid FLIR: no metadata encountered')

    flir_app1_bytes = b''
    for chunk_num in range(chunks_count + 1):
        flir_app1_bytes += chunks[chunk_num]

    flir_app1_stream = BytesIO(flir_app1_bytes)
    flir_app1_stream.seek(0)
    return flir_app1_stream


def parse_flir_chunk(stream: BinaryIO, chunks_count: Optional[int]) -> Optional[Tuple[int, int, bytes]]:
    """Parse flir chunk."""
    # Parse the chunk header. Headers are as follows (definition with example):
    #
    #     \xff\xe1<length: 2 bytes>FLIR\x00\x01<chunk nr: 1 byte><chunk count: 1 byte>
    #     \xff\xe1\xff\xfeFLIR\x00\x01\x01\x0b
    #
    # Meaning: Exif APP1, 65534 long, FLIR chunk 1 out of 12
    marker = stream.read(CHUNK_APP1_BYTES_COUNT)

    length_bytes = stream.read(CHUNK_LENGTH_BYTES_COUNT)
    length = int.from_bytes(length_bytes, 'big')
    length -= CHUNK_METADATA_LENGTH
    magic_flir = stream.read(CHUNK_MAGIC_BYTES_COUNT)

    if not (marker == APP1_MARKER and magic_flir == MAGIC_FLIR_DEF):
        # Seek back to just after byte b and continue searching for chunks
        stream.seek(-len(marker) - len(length_bytes) - len(magic_flir), 1)
        return None

    stream.seek(1, 1)  # skip 1 byte, unsure what it is for

    chunk_num = int.from_bytes(stream.read(CHUNK_NUM_BYTES_COUNT), 'big')
    chunks_tot = int.from_bytes(stream.read(CHUNK_TOT_BYTES_COUNT), 'big')

    # Remember total chunks to verify metadata consistency
    if chunks_count is None:
        chunks_count = chunks_tot

    if (  # Check whether chunk metadata is consistent
            chunks_tot is None or chunk_num < 0 or chunk_num > chunks_tot or chunks_tot != chunks_count
    ):
        raise ValueError(f'Invalid FLIR: inconsistent total chunks, should be 0 or greater, but is {chunks_tot}')

    return chunks_tot, chunk_num, stream.read(length + 1)


def parse_thermal(stream: BinaryIO, records: Dict[int, Tuple[int, int, int, int]]) -> np.ndarray:
    """Parse thermal."""
    record_idx_raw_data = 1
    raw_data_md = records[record_idx_raw_data]
    _, _, raw_data = parse_raw_data(stream, raw_data_md)
    return raw_data


def parse_flir_app1(stream: BinaryIO) -> Dict[int, Tuple[int, int, int, int]]:
    """Parse flir app1."""
    # 0x00 - string[4] file format ID = 'FFF\0'
    # 0x04 - string[16] file creator: seen '\0','MTX IR\0','CAMCTRL\0'
    # 0x14 - int32u file format version = 100
    # 0x18 - int32u offset to record directory
    # 0x1c - int32u number of entries in record directory
    # 0x20 - int32u next free index ID = 2
    # 0x24 - int16u swap pattern = 0 (?)
    # 0x28 - int16u[7] spares
    # 0x34 - int32u[2] reserved
    # 0x3c - int32u checksum

    # 1. Read 0x40 bytes and verify that its contents equals AFF\0 or FFF\0
    _ = stream.read(4)

    # 2. Read FLIR record directory metadata (ref 3)
    stream.seek(16, 1)
    _ = int.from_bytes(stream.read(4), 'big')
    record_dir_offset = int.from_bytes(stream.read(4), 'big')
    record_dir_entries_count = int.from_bytes(stream.read(4), 'big')
    stream.seek(28, 1)
    _ = int.from_bytes(stream.read(4), 'big')

    # 3. Read record directory (which is a FLIR record entry repeated
    # `record_dir_entries_count` times)
    stream.seek(record_dir_offset)
    record_dir_stream = BytesIO(stream.read(32 * record_dir_entries_count))

    # First parse the record metadata
    record_details: Dict[int, Tuple[int, int, int, int]] = {}
    for record_nr in range(record_dir_entries_count):
        record_dir_stream.seek(0)
        details = parse_flir_record_metadata(stream, record_nr)
        if details:
            record_details[details[1]] = details

    # Then parse the actual records
    # for (entry_idx, type, offset, length) in record_details:
    #     parse_record = record_parsers[type]
    #     stream.seek(offset)
    #     record = BytesIO(stream.read(length + 36))  # + 36 needed to find end
    #     parse_record(record, offset, length)

    return record_details


def parse_flir_record_metadata(stream: BinaryIO, record_nr: int) -> Optional[Tuple[int, int, int, int]]:
    """Parse flir record metadata."""
    # FLIR record entry (ref 3):
    # 0x00 - int16u record type
    # 0x02 - int16u record subtype: RawData 1=BE, 2=LE, 3=PNG; 1 for other record types
    # 0x04 - int32u record version: seen 0x64,0x66,0x67,0x68,0x6f,0x104
    # 0x08 - int32u index id = 1
    # 0x0c - int32u record offset from start of FLIR data
    # 0x10 - int32u record length
    # 0x14 - int32u parent = 0 (?)
    # 0x18 - int32u object number = 0 (?)
    # 0x1c - int32u checksum: 0 for no checksum
    entry = 32 * record_nr
    stream.seek(entry)
    record_type = int.from_bytes(stream.read(2), 'big')
    if record_type < 1:
        return None

    _ = int.from_bytes(stream.read(2), 'big')
    _ = int.from_bytes(stream.read(4), 'big')
    _ = int.from_bytes(stream.read(4), 'big')
    record_offset = int.from_bytes(stream.read(4), 'big')
    record_length = int.from_bytes(stream.read(4), 'big')
    _ = int.from_bytes(stream.read(4), 'big')
    _ = int.from_bytes(stream.read(4), 'big')
    _ = int.from_bytes(stream.read(4), 'big')
    return entry, record_type, record_offset, record_length


def parse_raw_data(stream: BinaryIO, metadata: Tuple[int, int, int, int]):
    """Parse raw data."""
    (_, _, offset, length) = metadata
    stream.seek(offset)

    stream.seek(2, 1)
    width = int.from_bytes(stream.read(2), 'little')
    height = int.from_bytes(stream.read(2), 'little')

    stream.seek(offset + 32)

    # Read the bytes with the raw thermal data and decode using PIL
    thermal_bytes = stream.read(length)
    thermal_stream = BytesIO(thermal_bytes)
    thermal_img = Image.open(thermal_stream)
    thermal_np = np.array(thermal_img)

    # Check shape
    if thermal_np.shape != (height, width):
        msg = f'Invalid FLIR: metadata\'s width and height don\'t match thermal data\'s actual width and height ({thermal_np.shape} vs ({height}, {width})'
        raise ValueError(msg)

    # FLIR PNG data is in the wrong byte order, fix that
    fix_byte_order = np.vectorize(lambda x: (x >> 8) + ((x & 0x00FF) << 8))
    thermal_np = fix_byte_order(thermal_np)

    return width, height, thermal_np


ABSOLUTE_ZERO = 273.15


class Thermal:
    # Camera Model Name
    DJI_XT2 = 'XT2'
    DJI_ZH20T = 'ZH20T'
    DJI_XTS = 'XT S'
    DJI_XTR = 'FLIR'

    FLIR_B60 = 'Flir b60'
    FLIR_E40 = 'FLIR E40'
    FLIR_T640 = 'FLIR T640'
    FLIR = 'FLIR'
    FLIR_DEFAULT = '*'
    FLIR_AX8 = 'FLIR AX8'

    DJI_M2EA = 'MAVIC2-ENTERPRISE-ADVANCED'
    DJI_H20N = 'ZH20N'
    DJI_M3T = 'M3T'
    DJI_M30T = 'M30T'

    # dirp_ret_code_e
    DIRP_SUCCESS = 0  # 0: Success (no error)
    DIRP_ERROR_MALLOC = -1  # -1: Malloc error
    DIRP_ERROR_POINTER_NULL = -2  # -2: NULL pointer input
    DIRP_ERROR_INVALID_PARAMS = -3  # -3: Invalid parameters input
    DIRP_ERROR_INVALID_RAW = -4  # -4: Invalid RAW in R-JPEG
    DIRP_ERROR_INVALID_HEADER = -5  # -5: Invalid header in R-JPEG
    DIRP_ERROR_INVALID_CURVE = -6  # -6: Invalid curve LUT in R-JPEG
    DIRP_ERROR_RJPEG_PARSE = -7  # -7: Parse error for R-JPEG data
    DIRP_ERROR_SIZE = -8  # -8: Wrong size input
    DIRP_ERROR_INVALID_HANDLE = -9  # -9: Invalid handle input
    DIRP_ERROR_FORMAT_INPUT = -10  # -10: Wrong input image format
    DIRP_ERROR_FORMAT_OUTPUT = -11  # -11: Wrong output image format
    DIRP_ERROR_UNSUPPORTED_FUNC = -12  # -12: Unsupported function called
    DIRP_ERROR_NOT_READY = -13  # -13: Some preliminary conditions not meet
    DIRP_ERROR_ACTIVATION = -14  # -14: SDK activate failed
    DIRP_ERROR_ADVANCED = -32  # -32: Advanced error codes which may be smaller than this value

    def __init__(
            self,
            dtype=np.float32,
    ):
        """
        Load exiftool/DJI SDK.

        Args:
            dtype: np.float32 or np.int16. parse R-JPEG files in the format specified by dtype

        Raises
        ------
        OSError
            When DJI SDK cannot be loaded, a OSError is thrown.

            * File does not exist
            * DJI SDK does not match the operating system

        AssertionError
            * DJI SDK does not exist
            * dtype not as expected
            * DJI SDK cannot be registered properly

        """
        assert dtype.__name__ in {np.float32.__name__, np.int16.__name__}

        self._dtype = dtype
        self._support_camera_model = {
            Thermal.DJI_XT2, Thermal.DJI_ZH20T, Thermal.DJI_XTS, Thermal.DJI_XTR,
            Thermal.FLIR_B60, Thermal.FLIR_E40, Thermal.FLIR_T640,
            Thermal.FLIR, Thermal.FLIR_DEFAULT, Thermal.FLIR_AX8,
            Thermal.DJI_M2EA,
            Thermal.DJI_H20N, Thermal.DJI_M3T, Thermal.DJI_M30T,
        }

        (
            self._filepath_dirp,
            self._filepath_dirp_sub,
            self._filepath_iirp,
            self._filepath_exiftool,
        ) = get_default_filepaths()

        try:
            self._dll_dirp = CDLL(self._filepath_dirp)
            self._dll_dirp_sub = CDLL(self._filepath_dirp_sub)
            self._dll_iirp = CDLL(self._filepath_iirp)
        except OSError:
            print('Unable to load the system C library')
            sys.exit()

        # NOTE: The following code is for dji_thermal_sdk_v1.0
        # # Register SDK for the application.
        # # User must call this function once at initialize stage.
        # # Key string is "DJI_TSDK\0".
        # self._dirp_register_app = self._thermal_dll.dirp_register_app
        # self._dirp_register_app.argtypes = [c_char_p]
        # self._dirp_register_app.restype = c_int32
        #
        # ret_code = self._dirp_register_app(cast(create_string_buffer(b'DJI_TSDK'), c_char_p))
        # assert ret_code == Thermal.DIRP_SUCCESS

        self._dirp_set_verbose_level = self._dll_dirp.dirp_set_verbose_level
        self._dirp_set_verbose_level.argtypes = [c_int]
        self._dirp_set_verbose_level(DIRP_VERBOSE_LEVEL_NONE)

        # Create a new DIRP handle with specified R-JPEG binary data.
        # The R-JPEG binary data buffer must remain valid until the handle is destroyed.
        # The DIRP API library will create some alloc buffers for inner usage.
        # So the application should reserve enough stack size for the library.
        self._dirp_create_from_rjpeg = self._dll_dirp.dirp_create_from_rjpeg
        self._dirp_create_from_rjpeg.argtypes = [POINTER(c_uint8), c_int32, POINTER(DIRP_HANDLE)]
        self._dirp_create_from_rjpeg.restype = c_int32

        # Destroy the DIRP handle.
        self._dirp_destroy = self._dll_dirp.dirp_destroy
        self._dirp_destroy.argtypes = [DIRP_HANDLE]
        self._dirp_destroy.restype = c_int32

        self._dirp_get_rjpeg_version = self._dll_dirp.dirp_get_rjpeg_version
        self._dirp_get_rjpeg_version.argtypes = [DIRP_HANDLE, POINTER(dirp_rjpeg_version_t)]
        self._dirp_get_rjpeg_version.restype = c_int32

        self._dirp_get_rjpeg_resolution = self._dll_dirp.dirp_get_rjpeg_resolution
        self._dirp_get_rjpeg_resolution.argtypes = [DIRP_HANDLE, POINTER(dirp_resolotion_t)]
        self._dirp_get_rjpeg_resolution.restype = c_int32

        # Get orignial/custom temperature measurement parameters.
        self._dirp_get_measurement_params = self._dll_dirp.dirp_get_measurement_params
        self._dirp_get_measurement_params.argtypes = [DIRP_HANDLE, POINTER(dirp_measurement_params_t)]
        self._dirp_get_measurement_params.restype = c_int32

        # Set custom temperature measurement parameters.
        self._dirp_set_measurement_params = self._dll_dirp.dirp_set_measurement_params
        self._dirp_set_measurement_params.argtypes = [DIRP_HANDLE, POINTER(dirp_measurement_params_t)]
        self._dirp_set_measurement_params.restype = c_int32

        # Measure temperature of whole thermal image with RAW data in R-JPEG.
        # Each INT16 pixel value represents ten times the temperature value in Celsius. In other words,
        # each LSB represents 0.1 degrees Celsius.
        self._dirp_measure = self._dll_dirp.dirp_measure
        self._dirp_measure.argtypes = [DIRP_HANDLE, POINTER(c_int16), c_int32]
        self._dirp_measure.restype = c_int32

        # Measure temperature of whole thermal image with RAW data in R-JPEG.
        # Each float32 pixel value represents the real temperature in Celsius.
        self._dirp_measure_ex = self._dll_dirp.dirp_measure_ex
        self._dirp_measure_ex.argtypes = [DIRP_HANDLE, POINTER(c_float), c_int32]
        self._dirp_measure_ex.restype = c_int32

    def parse(
            self,
            filepath_image: str,
    ) -> np.ndarray:
        """
        Parser infrared camera data as `NumPy` data.

        Args:
            filepath_image: str, relative path of R-JPEG image

        Returns:
            np.ndarray: temperature array

        Raises
        ------
            AssertionError
                * wrong parameter type
                * R-JPEG file does not exist
                * field missing
                * unsupported camera type
        """

        assert isinstance(filepath_image, str) and os.path.exists(
            filepath_image), f'Check if the file exists: {filepath_image}.'
        meta = subprocess.Popen([self._filepath_exiftool, filepath_image], stdout=subprocess.PIPE).communicate()[0]
        meta = meta.decode('utf8').replace('\r', '')
        meta_json = dict([
            (field.split(':')[0].strip(), field.split(':')[1].strip()) for field in meta.split('\n') if ':' in field
        ])
        assert 'Camera Model Name' in meta_json, f'{filepath_image} `Camera Model Name` field is missing'
        camera_model = meta_json['Camera Model Name']
        assert camera_model in self._support_camera_model or Thermal.FLIR in camera_model, f'Unsupported camera type: {camera_model}'
        if camera_model in {
            Thermal.FLIR,
            Thermal.FLIR_DEFAULT,
            Thermal.FLIR_T640,
            Thermal.FLIR_E40,
            Thermal.FLIR_B60,
            Thermal.FLIR_AX8,
            Thermal.DJI_XT2,
            Thermal.DJI_XTR,
        } or Thermal.FLIR in camera_model:
            kwargs = dict((name, float(meta_json[key])) for name, key in [
                ('emissivity', 'Emissivity'),
                ('ir_window_transmission', 'IR Window Transmission'),
                ('planck_r1', 'Planck R1'),
                ('planck_b', 'Planck B'),
                ('planck_f', 'Planck F'),
                ('planck_o', 'Planck O'),
                ('planck_r2', 'Planck R2'),
                ('ata1', 'Atmospheric Trans Alpha 1'),
                ('ata2', 'Atmospheric Trans Alpha 2'),
                ('atb1', 'Atmospheric Trans Beta 1'),
                ('atb2', 'Atmospheric Trans Beta 2'),
                ('atx', 'Atmospheric Trans X'),
            ] if key in meta_json)
            for name, key in [
                ('object_distance', 'Object Distance'),
                ('atmospheric_temperature', 'Atmospheric Temperature'),
                ('reflected_apparent_temperature', 'Reflected Apparent Temperature'),
                ('ir_window_temperature', 'IR Window Temperature'),
                ('relative_humidity', 'Relative Humidity'),
            ]:
                if key in meta_json:
                    kwargs[name] = float(meta_json[key][:-2])
            return self.parse_flir(
                filepath_image=filepath_image,
                **kwargs,
            )
        elif camera_model in {
            Thermal.DJI_ZH20T,
            Thermal.DJI_XTS,

            Thermal.DJI_M2EA,
            Thermal.DJI_H20N,
            Thermal.DJI_M3T,
            Thermal.DJI_M30T,
        }:
            for key in ['Image Height', 'Image Width']:
                assert key in meta_json, f'The `{key}` field is missing'
            kwargs = dict((name, float(re.findall(r'\d+\.\d+|\d+', meta_json[key])[0])) for name, key in [
                ('object_distance', 'Object Distance'),
                ('relative_humidity', 'Relative Humidity'),
                ('emissivity', 'Emissivity'),
                ('reflected_apparent_temperature', 'Reflected Temperature'),
            ] if key in meta_json)
            # NOTE: the jpeg image of M30T has a fixed size of 640x512
            if camera_model != Thermal.DJI_M30T:
                kwargs['image_height'] = int(meta_json['Image Height'])
                kwargs['image_width'] = int(meta_json['Image Width'])
            if 'emissivity' in kwargs:
                kwargs['emissivity'] /= 100
            if camera_model in [
                Thermal.DJI_M2EA,
                Thermal.DJI_H20N,
                Thermal.DJI_M3T,
                Thermal.DJI_M30T,
            ]:
                kwargs['m2ea_mode'] = True,
            return self.parse_dirp2(
                filepath_image=filepath_image,
                **kwargs,
            )

    def parse_flir(
            self,
            filepath_image: str,
            # params
            emissivity: float = 1.0,
            object_distance: float = 1.0,
            atmospheric_temperature: float = 20.0,
            reflected_apparent_temperature: float = 20.0,
            ir_window_temperature: float = 20.0,
            ir_window_transmission: float = 1.0,
            relative_humidity: float = 50.0,
            # planck constants
            planck_r1: float = 21106.77,
            planck_b: float = 1501.0,
            planck_f: float = 1.0,
            planck_o: float = -7340.0,
            planck_r2: float = 0.012545258,
            # constants
            ata1: float = 0.006569,
            ata2: float = 0.01262,
            atb1: float = -0.002276,
            atb2: float = -0.00667,
            atx: float = 1.9,
    ) -> np.ndarray:
        """
        Parser infrared camera data as `NumPy` data`.

        Equations to convert to temperature see http://130.15.24.88/exiftool/forum/index.php/topic,4898.60.html or https://github.com/gtatters/Thermimage/blob/master/R/raw2temp.R

        Args:
            filepath_image: str, relative path of R-JPEG image
            emissivity: float, E: Emissivity - default 1, should be ~0.95 to 0.97 depending on source
            object_distance: float, OD: Object distance in metres
            atmospheric_temperature: float, ATemp: atmospheric temperature for tranmission loss - one value from FLIR file (oC) - default = RTemp
            reflected_apparent_temperature: float, RTemp: apparent reflected temperature - one value from FLIR file (oC), default 20C
            ir_window_temperature: float, Infrared Window Temperature - default = RTemp (oC)
            ir_window_transmission: float, Infrared Window transmission - default 1.  likely ~0.95-0.96. Should be empirically determined.
            relative_humidity: float, Relative humidity - default 50%
            Calibration Constants                                          (A FLIR SC660, A FLIR T300(25o), T300(telephoto), A Mikron 7515)
            planck_r1: float, PlanckR1 calibration constant from FLIR file  21106.77       14364.633         14906.216       21106.77
            planck_b: float, PlanckB calibration constant from FLIR file    1501           1385.4            1396.5          9758.743281
            planck_f: float, PlanckF calibration constant from FLIR file    1              1                 1               29.37648768
            planck_o: float, PlanckO calibration constant from FLIR file    -7340          -5753             -7261           1278.907078
            planck_r2: float, PlanckR2 calibration constant form FLIR file  0.012545258    0.010603162       0.010956882     0.0376637583528285
            ata1: float, Atmospheric Trans Alpha 1  0.006569 constant for calculating humidity effects on transmission
            ata2: float, Atmospheric Trans Alpha 2  0.012620 constant for calculating humidity effects on transmission
            atb1: float, Atmospheric Trans Beta 1  -0.002276 constant for calculating humidity effects on transmission
            atb2: float, Atmospheric Trans Beta 2  -0.006670 constant for calculating humidity effects on transmission
            atx: float, Atmospheric Trans X        1.900000 constant for calculating humidity effects on transmission

        Returns:
            np.ndarray: temperature array

        References:
            * from https://github.com/gtatters/Thermimage/blob/master/R/raw2temp.R
            * from https://github.com/detecttechnologies/thermal_base
            * from https://github.com/aloisklink/flirextractor/blob/1fc759808c747ad5562a9ddb3cd75c4def8a3f69/flirextractor/raw_temp_to_celcius.py
        """
        thermal_img_bytes = subprocess.check_output([
            self._filepath_exiftool, '-RawThermalImage', '-b', filepath_image
        ])

        thermal_img_stream = BytesIO(thermal_img_bytes)
        thermal_img = Image.open(thermal_img_stream)
        img_format = thermal_img.format

        # checking for the type of the decoded images
        if img_format == 'TIFF':
            raw = np.array(thermal_img)
        elif img_format == 'PNG':
            raw = unpack(filepath_image)
        else:
            raise ValueError

        # transmission through window (calibrated)
        emiss_wind = 1 - ir_window_transmission
        refl_wind = 0
        # transmission through the air
        h2o = (relative_humidity / 100) * np.exp(
            1.5587
            + 0.06939 * atmospheric_temperature
            - 0.00027816 * atmospheric_temperature ** 2
            + 0.00000068455 * atmospheric_temperature ** 3
        )
        tau1 = atx * np.exp(-np.sqrt(object_distance / 2) * (ata1 + atb1 * np.sqrt(h2o))) + (1 - atx) * np.exp(
            -np.sqrt(object_distance / 2) * (ata2 + atb2 * np.sqrt(h2o))
        )
        tau2 = atx * np.exp(-np.sqrt(object_distance / 2) * (ata1 + atb1 * np.sqrt(h2o))) + (1 - atx) * np.exp(
            -np.sqrt(object_distance / 2) * (ata2 + atb2 * np.sqrt(h2o))
        )
        # radiance from the environment
        raw_refl1 = planck_r1 / \
            (planck_r2 * (np.exp(planck_b / (reflected_apparent_temperature + ABSOLUTE_ZERO)) - planck_f)) - planck_o
        # Reflected component
        raw_refl1_attn = (1 - emissivity) / emissivity * raw_refl1

        # Emission from atmosphere 1
        raw_atm1 = (planck_r1 / (planck_r2 * (np.exp(planck_b / (atmospheric_temperature + ABSOLUTE_ZERO)) - planck_f)) - planck_o)
        # attenuation for atmospheric 1 emission
        raw_atm1_attn = (1 - tau1) / emissivity / tau1 * raw_atm1

        # Emission from window due to its own temp
        raw_wind = (planck_r1 / (planck_r2 * (np.exp(planck_b / (ir_window_temperature + ABSOLUTE_ZERO)) - planck_f)) - planck_o)
        # Componen due to window emissivity
        raw_wind_attn = (emiss_wind / emissivity / tau1 / ir_window_transmission * raw_wind)

        # Reflection from window due to external objects
        raw_refl2 = (planck_r1 / (planck_r2 *
                     (np.exp(planck_b / (reflected_apparent_temperature + ABSOLUTE_ZERO)) - planck_f)) - planck_o)
        # component due to window reflectivity
        raw_refl2_attn = (refl_wind / emissivity / tau1 / ir_window_transmission * raw_refl2)

        # Emission from atmosphere 2
        raw_atm2 = (planck_r1 / (planck_r2 * (np.exp(planck_b / (atmospheric_temperature + ABSOLUTE_ZERO)) - planck_f)) - planck_o)
        # attenuation for atmospheric 2 emission
        raw_atm2_attn = ((1 - tau2) / emissivity / tau1 / ir_window_transmission / tau2 * raw_atm2)

        raw_obj = (
            raw / emissivity / tau1 / ir_window_transmission / tau2
            - raw_atm1_attn
            - raw_atm2_attn
            - raw_wind_attn
            - raw_refl1_attn
            - raw_refl2_attn
        )
        val_to_log = planck_r1 / (planck_r2 * (raw_obj + planck_o)) + planck_f
        if any(val_to_log.ravel() < 0):
            raise ValueError(f'Image seems to be corrupted: {filepath_image}')
        # temperature from radiance
        temperature = planck_b / np.log(val_to_log) - ABSOLUTE_ZERO
        return np.array(temperature, self._dtype)

    def parse_dirp2(
            self,
            filepath_image: str,
            image_height: int = 512,
            image_width: int = 640,
            object_distance: float = 5.0,
            relative_humidity: float = 70.0,
            emissivity: float = 1.0,
            reflected_apparent_temperature: float = 23.0,
            m2ea_mode: bool = False,
    ):
        """
        Parser infrared camera data as `NumPy` data`.
        `dirp2` means `DJI IR Processing Version 2nd`.

        Args:
            filepath_image: str, relative path of R-JPEG image
            image_height: float, image height
            image_width: float, image width
            object_distance: float, The distance to the target. Value range is [1~25] meters.
            relative_humidity: float, The relative humidity of the environment. Value range is [20~100] percent. Defualt value is 70%.
            emissivity: float, How strongly the target surface is emitting energy as thermal radiation. Value range is [0.10~1.00].
            reflected_apparent_temperature: float, Reflected temperature in Celsius. The surface of the target that is measured could reflect the energy radiated by the surrounding objects. Value range is [-40.0~500.0]
            m2ea_mode: bool

        Returns:
            np.ndarray: temperature array

        References:
            * [DJI Thermal SDK](https://www.dji.com/cn/downloads/softwares/dji-thermal-sdk)
        """
        with open(filepath_image, 'rb') as file:
            raw = file.read()
            raw_size = c_int32(len(raw))
            raw_c_uint8 = cast(raw, POINTER(c_uint8))

        handle = DIRP_HANDLE()
        rjpeg_version = dirp_rjpeg_version_t()
        rjpeg_resolotion = dirp_resolotion_t()

        return_status = self._dirp_create_from_rjpeg(raw_c_uint8, raw_size, handle)
        assert return_status == Thermal.DIRP_SUCCESS, f'dirp_create_from_rjpeg error {filepath_image}:{return_status}'
        assert self._dirp_get_rjpeg_version(handle, rjpeg_version) == Thermal.DIRP_SUCCESS
        assert self._dirp_get_rjpeg_resolution(handle, rjpeg_resolotion) == Thermal.DIRP_SUCCESS

        if not m2ea_mode:
            params = dirp_measurement_params_t()
            params_point = pointer(params)
            return_status = self._dirp_get_measurement_params(handle, params_point)
            assert return_status == Thermal.DIRP_SUCCESS, f'dirp_get_measurement_params error {filepath_image}:{return_status}'

            if isinstance(object_distance, (float, int)):
                params.distance = object_distance
            if isinstance(relative_humidity, (float, int)):
                params.humidity = relative_humidity
            if isinstance(emissivity, (float, int)):
                params.emissivity = emissivity
            if isinstance(reflected_apparent_temperature, (float, int)):
                params.reflection = reflected_apparent_temperature

            return_status = self._dirp_set_measurement_params(handle, params)
            assert return_status == Thermal.DIRP_SUCCESS, f'dirp_set_measurement_params error {filepath_image}:{return_status}'

        if self._dtype.__name__ == np.float32.__name__:
            data = np.zeros(image_width * image_height, dtype=np.float32)
            data_ptr = data.ctypes.data_as(POINTER(c_float))
            data_size = c_int32(image_width * image_height * sizeof(c_float))
            assert self._dirp_measure_ex(handle, data_ptr, data_size) == Thermal.DIRP_SUCCESS
            temp = np.reshape(data, (image_height, image_width))
        elif self._dtype.__name__ == np.int16.__name__:
            data = np.zeros(image_width * image_height, dtype=np.int16)
            data_ptr = data.ctypes.data_as(POINTER(c_int16))
            data_size = c_int32(image_width * image_height * sizeof(c_int16))
            assert self._dirp_measure(handle, data_ptr, data_size) == Thermal.DIRP_SUCCESS
            temp = np.reshape(data, (image_height, image_width)) / 10
        else:
            raise ValueError
        assert self._dirp_destroy(handle) == Thermal.DIRP_SUCCESS

        return np.array(temp, dtype=self._dtype)
