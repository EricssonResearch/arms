#!/usr/bin/env python3

"""setuptools installer script for arms."""

from setuptools import setup, find_packages

setup(
    name='arms',
    version='0.1.0',
    license='Apache-2.0',
    description='Managing the task of replacing a malfunctioning SFP module.',
    author='HK team 2018',

    packages=find_packages(),

    install_requires=['pytest', 'pytest-cov'],
    tests_require=['pytest', 'pytest-cov'],
)
