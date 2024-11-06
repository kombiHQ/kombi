import os
from .TaskWrapper import TaskWrapper
from .DCCTaskWrapper import DCCTaskWrapper


class HoudiniTaskWrapper(DCCTaskWrapper):
    """
    Performs a task inside houdini.
    """

    __houdiniHythonExecutable = os.environ.get(
        'KOMBI_HYTHON_EXECUTABLE',
        'hython'
    )

    __houdiniHythonArgs = ""

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

        return '{} "{}" {}'.format(
            self.__houdiniHythonExecutable,
            scriptLoaderPath,
            self.__houdiniHythonArgs
        )

    @classmethod
    def _hookName(cls):
        """
        For re-implementation: should return a string containing the name used for the hook registered in basetools.
        """
        return "houdini"


# registering task wrapper
TaskWrapper.register(
    'houdini',
    HoudiniTaskWrapper
)
