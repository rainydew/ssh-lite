# coding: utf-8
# author: Rainy Chan
# mailto: rainydew@qq.com
import sys
if (3, 4, 10) < sys.version_info < (4, 0, 0):
    from .ssh_lite_py3 import *
elif (2, 6, 0) < sys.version_info < (3, 0, 0):
    from .ssh_lite_py2 import *
