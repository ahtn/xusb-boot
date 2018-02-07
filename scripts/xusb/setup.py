#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright 2018 jem@seethis.link
# Licensed under the MIT license (http://opensource.org/licenses/MIT)

from setuptools import setup

setup(
    name = 'xusb',
    version = '0.0.0',
    description = "Python library for Xmega xusb bootloader",
    url = "http://github.com/ahtn/xusb-boot",
    author = "jem",
    author_email = "jem@seethis.link",
    license = 'MIT',
    packages = ['xusb'],
    install_requires = ['hexdump', 'intelhex', 'easyhid'],
    keywords = ['xmega', 'usb', 'hid', 'avr', 'bootloader'],
    zip_safe = False
)
