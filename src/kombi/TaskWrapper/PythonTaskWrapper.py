import os
from .SubprocessTaskWrapper import SubprocessTaskWrapper

class PythonTaskWrapper(SubprocessTaskWrapper):
    """
    Runs a task through python.
    """

    __pythonExecutable = os.environ.get(
        'KOMBI_PYTHON_EXECUTABLE',
        'python'
    )

    def __init__(self, *args, **kwargs):
        """
        Create a python task wrapper object.
        """
        super(PythonTaskWrapper, self).__init__(*args, **kwargs)

        self.setOption(
            'executableName',
            self.__pythonExecutable
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

        return '{} {}'.format(
            self.option('executableName'),
            scriptLoaderPath
        )


class _Python3TaskWrapper(PythonTaskWrapper):
    """
    Forces a task to be performed using python 3.
    """

    def __init__(self, *args, **kwargs):
        """
        Create a python 3 task wrapper object.
        """
        super(PythonTaskWrapper, self).__init__(*args, **kwargs)

        self.setOption(
            'executableName',
            os.environ.get(
                'KOMBI_PYTHON3_EXECUTABLE',
                'python3'
            )
        )


# registering task wrappers
SubprocessTaskWrapper.register(
    'python',
    PythonTaskWrapper
)

# also registering the subprocess
SubprocessTaskWrapper.register(
    'subprocess',
    PythonTaskWrapper
)

# specific for python 3.x
SubprocessTaskWrapper.register(
    'python3',
    _Python3TaskWrapper
)
