#!/usr/bin/env python3
# coding: utf-8
from distutils.core import setup
from os import path

this_directory = path.abspath(path.dirname(__file__))

try:
    import pypandoc
    long_description = pypandoc.convert('README.md', 'rst')
except:
    long_description = ""

setup(
    name='ssh-lite',
    version='1.7',
    description='An easy encapsulation for paramiko library which contains only common operations (ssh, sftp, expect..)',
    author='Rainy Chan',
    author_email='rainydew@qq.com',
    url='https://github.com/rainydew/ssh-lite',
    py_modules=['ssh_lite'],
    install_requires=['paramiko>=2.5.0'],
    keywords='ssh sftp easy paramiko non-blocking',
    long_description=long_description,
    python_requires=">=3.5"
)
