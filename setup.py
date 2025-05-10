#!/usr/bin/env python3
from setuptools import setup, find_packages

setup(
    name="garmin_downloader",
    version="1.0.0",
    description="Downloads health data from Garmin Connect",
    packages=find_packages(),
    install_requires=[
        "garminconnect",
    ],
    python_requires=">=3.6",
)
