import os
import sys
import functools
import traceback
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

    def __init__(self, *args, **kwargs):
        """
        Create a maya task wrapper object.
        """
        super().__init__(*args, **kwargs)

        self.setOption(
            'batch',
            True
        )

        # This option waits a few seconds for Maya to initialize all plugins and resources.
        # This issue has been observed when running Maya with UI support,
        # where it may require around 10 seconds to fully initialize.
        self.setOption(
            'waitSeconds',
            0
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

        return '{} -file "{}"{} -command "python(\\"import kombi; kombi.TaskWrapper.TaskWrapper.create(\'maya\').runSerializedTask({}, {})\\")"'.format(
            self.__mayaBatchExecutable,
            dummyMayaFilePath,
            ' -batch' if self.option('batch') else ' -nosplash',
            int(self.option('batch')),
            int(self.option('waitSeconds'))
        )

    @staticmethod
    def runSerializedTask(isBatch=True, waitSeconds=0):
        """
        Run a serialized task defined in the environment during SubprocessTaskWrapper._perform.
        """
        from maya import utils, cmds

        if isBatch:
            super(MayaTaskWrapper).runSerializedTask()
            return

        def __executeWhenIsIdle():
            # we want to redirect all prints to the stdout (otherwise
            # they will go to the script editor only)
            sys.stdout = sys.__stdout__
            exitCode = 0
            try:
                DCCTaskWrapper.runSerializedTask()
            except Exception as err:
                exitCode = 1
                # printing the exception. This is necessary to make
                # the error visible in the stdout
                print(traceback.format_exc())
                raise err
            finally:
                # we need to also flush the stdout before closing
                sys.stdout.flush()

                # quitting maya
                cmds.quit(f=True, exitCode=exitCode)

        # when waitSeconds is non-zero, schedule __executeWhenIsIdle to run after the specified delay
        # (in seconds) using QTimer.singleShot, deferring execution until the app is idle
        if waitSeconds != 0:
            from Qt import QtCore
            QtCore.QTimer.singleShot(waitSeconds * 1000, functools.partial(utils.executeDeferred, __executeWhenIsIdle))
        else:
            utils.executeDeferred(__executeWhenIsIdle)

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
