import os
from .TaskWrapper import TaskWrapper
from .DCC import DCC

class Maya(DCC):
    """
    Performs a task inside maya.
    """

    __mayaExecutable = os.environ.get(
        'KOMBI_MAYA_EXECUTABLE',
        'maya'
    )

    def _command(self):
        """
        For re-implementation: should return a string which is executed as subprocess.
        """
        return '{} -batch -command "python(\\"import kombi; kombi.TaskWrapper.Subprocess.runSerializedTask()\\")"'.format(
            self.__mayaExecutable
        )

    @classmethod
    def _hookName(cls):
        """
        For re-implementation: should return a string containing the name used for the hook registered in basetools.
        """
        return "maya"


# registering task wrapper
TaskWrapper.register(
    'maya',
    Maya
)
