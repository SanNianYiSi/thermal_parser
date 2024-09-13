import os
from setuptools import setup, find_packages


def format_data_files():
    data_files = [
        ('plugins', [os.path.join('plugins', 'exiftool-12.35.exe')]),
    ]
    # Iterate through all files and subdirectories in a directory
    for root, _, filenames in os.walk(os.path.join('plugins', 'dji_thermal_sdk_v1.4_20220929')):
        filepaths = []
        for filename in filenames:
            if any(filename.endswith(v) for v in ['.dll', '.lib', '.so', '.ini', '.txt']):
                filepaths.append(os.path.join(root, filename))
        if filepaths:
            data_files.append((root, filepaths))
    return data_files


setup(
    name='thermal_parser',
    version='20240912',
    description='FLIR/DJI IR Camera Data Parser, Python Version',
    url='https://github.com/roy-shudipto/thermal_parser.git',
    author='SanNianYiSi',
    author_email='CcoO296y@163.com',
    license='MIT Licence',
    packages=find_packages(),
    data_files=format_data_files(),
    install_requires=[
        'numpy',
        'Pillow',
    ],
    classifiers=[
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'Intended Audience :: Developers',
        'Natural Language :: Chinese (Simplified)',
        'Natural Language :: English',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Topic :: Software Development :: Libraries'
    ],
)
