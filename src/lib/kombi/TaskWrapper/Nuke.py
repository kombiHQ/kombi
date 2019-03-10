import os
from .TaskWrapper import TaskWrapper
from .DCC import DCC

class Nuke(DCC):
    """
    Performs a task inside nuke.
    """

    __nukeExecutable = os.environ.get(
        'KOMBI_NUKE_EXECUTABLE',
        'nuke'
    )
    __nukeArgs = os.environ.get(
        'KOMBI_NUKE_ARGS',
        '-x'
    )

    def _command(self):
        """
        For re-implementation: should return a string which is executed as subprocess.
        """
        scriptLoaderPath = os.path.join(
            os.path.dirname(
                os.path.realpath(__file__)
            ),
            'auxiliary',
            'runSerializedTask.py'
        )

        return '{} {} -t "{}" --log-level error'.format(
            self.__nukeExecutable,
            self.__nukeArgs,
            scriptLoaderPath
        )

    @classmethod
    def _hookName(cls):
        """
        For re-implementation: should return a string containing the name used for the hook registered in basetools.
        """
        return "nuke"


# registering task wrapper
TaskWrapper.register(
    'nuke',
    Nuke
)
