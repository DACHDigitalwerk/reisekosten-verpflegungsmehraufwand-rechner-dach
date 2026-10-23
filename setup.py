#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

setup(
    name="reisekosten-dach",
    version="2026.1.0",
    description="DACH Reisekosten-, Verpflegungsmehraufwand- & Pendlerpauschalen-Rechner 2026",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    author="DACH Digitalwerk",
    author_email="dach.digitalwerk@gmail.com",
    url="https://github.com/DACHDigitalwerk/reisekosten-verpflegungsmehraufwand-rechner-dach",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    entry_points={
        "console_scripts": [
            "dach-spesen=reisekosten_dach.cli:main",
        ],
    },
)
