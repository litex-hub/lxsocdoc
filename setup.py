#!/usr/bin/env python3

import sys
from setuptools import setup
from setuptools import find_packages


if sys.version_info[:3] < (3, 5):
    raise SystemExit("You need Python 3.5+")


setup(
    name="lxsocdoc",
    description="Document System-on-Chip for LiteX ",
    long_description=open("README.md").read(),
    author="Sean Cross",
    author_email="sean@xobs.io",
    url="http://xobs.io",
    download_url="https://github.com/xobs/lxsocdoc",
    license="BSD",
    platforms=["Any"],
    keywords="HDL ASIC FPGA hardware design",
    classifiers=[
        "Topic :: Scientific/Engineering :: Electronic Design Automation (EDA)",
        "Environment :: Console",
        "Development Status :: Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
    ],
    packages=find_packages(exclude=("static*")),
    install_requires=["sphinx", "sphinxcontrib-wavedrom"],
    include_package_data=True,
)
