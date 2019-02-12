import sys

if sys.version_info > (3, 0):
    from .python3 import *
else:
    from .python2 import *
