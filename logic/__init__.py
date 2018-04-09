
""" Requires Python >= 3.5, syntax error otherwise """
import sys
if sys.version_info[0] < 3 or sys.version_info[1] < 5:
    print('This module requires at least python3.5')
    quit()

from .logic import *

