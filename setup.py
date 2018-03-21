#!/usr/bin/env python3
from setuptools import setup

setup(name="SVGCode",
      version="0.0.1",
      description="GCode export for svgwrite",
      author="Jonas L. B.",
      author_email="drixi.b@gmail.com",
      url="",
      packages=["svgcode"],
      install_requires=[
           "svgwrite",
      ],
      )
