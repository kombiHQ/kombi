import tempfile
import uuid
import os
from ..Template import Template

class _System(object):
    """
    Basic system functions.
    """

    @staticmethod
    def tmp():
        """
        Return the location of the temporary directory.
        """
        return tempfile.gettempdir()

    @staticmethod
    def tmpdir():
        """
        Return a new temporary directory path (under the OS temp location).
        """
        path = os.path.join(
            tempfile.gettempdir(),
            str(uuid.uuid4())
        )

        return path

    @staticmethod
    def env(name, defaultValue=''):
        """
        Return the value of an environment variable.
        """
        return os.environ.get(name, defaultValue)


# registering template procedures
Template.registerProcedure(
    'tmp',
    _System.tmp
)

Template.registerProcedure(
    'tmpdir',
    _System.tmpdir
)

Template.registerProcedure(
    'env',
    _System.env
)
