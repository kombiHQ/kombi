import os
from .TaskWrapper import TaskWrapper
from .DCCTaskWrapper import DCCTaskWrapper

class MayaTaskWrapper(DCCTaskWrapper):
    """
    Performs a task inside maya.
    """

    __mayaBatchExecutable = os.environ.get(
        'KOMBI_MAYA_BATCH_EXECUTABLE',
        'maya'
    )

    def _command(self):
        """
        For re-implementation: should return a string which is executed as subprocess.
        """
        dummyMayaFilePath = os.path.join(
            os.path.dirname(
                os.path.realpath(__file__)
            ),
            'auxiliary',
            'dummy.ma'
        )

        return '{} -file "{}" -batch -command "python(\\"import kombi; kombi.TaskWrapper.SubprocessTaskWrapper.runSerializedTask()\\")"'.format(
            self.__mayaBatchExecutable,
            dummyMayaFilePath
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
    MayaTaskWrapper
)
