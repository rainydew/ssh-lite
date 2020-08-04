#!/usr/bin/env python3
# coding: utf-8
import ssl
ssl._create_default_https_context = ssl._create_unverified_context
# on MacOS 10.15.5 it returns
# <urlopen error [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed (_ssl.c:852)>
# without setting this

from distutils.core import setup
from os import path

this_directory = path.abspath(path.dirname(__file__))

try:
    import pypandoc
    long_description = pypandoc.convert('README.md', 'rst')
    print("successfully generated docs")
except:
    long_description = ""

setup(
    name='ssh-lite',
    version='1.9',
    description='An easy encapsulation for paramiko library which contains only common operations (ssh, sftp, expect..)',
    author='Rainy Chan',
    author_email='rainydew@qq.com',
    url='https://github.com/rainydew/ssh-lite',
    packages=['ssh_lite'],
    install_requires=['paramiko>=2.5.0'],
    keywords='ssh sftp easy paramiko non-blocking',
    long_description=long_description,
    python_requires=">=2.6, !=3.0.*, !=3.1.*, !=3.2.*, !=3.3.*, !=3.4.*"
)
