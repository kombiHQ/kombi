"""
Basic system functions.
"""

import tempfile
import uuid
import os
from ..Template import Template

def tmp():
    """
    Return the location of the temporary directory.
    """
    return tempfile.gettempdir()

def tmpdir():
    """
    Return a new temporary directory path (under the OS temp location).
    """
    path = os.path.join(
        tempfile.gettempdir(),
        str(uuid.uuid4())
    )

    return path

def env(name, defaultValue=''):
    """
    Return the value of an environment variable.
    """
    return os.environ.get(name, defaultValue)


# registering template procedures
Template.registerProcedure(
    'tmp',
    tmp
)

Template.registerProcedure(
    'tmpdir',
    tmpdir
)

Template.registerProcedure(
    'env',
    env
)
