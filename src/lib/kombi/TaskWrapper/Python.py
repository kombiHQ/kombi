import os
from .Subprocess import Subprocess

class Python(Subprocess):
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
        super(Python, self).__init__(*args, **kwargs)

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


class _Python2(Python):
    """
    Forces a task to be performed using python 2.
    """

    def __init__(self, *args, **kwargs):
        """
        Create a python 2 task wrapper object.
        """
        super(Python, self).__init__(*args, **kwargs)

        self.setOption(
            'executableName',
            os.environ.get(
                'KOMBI_PYTHON2_EXECUTABLE',
                'python2'
            )
        )

class _Python3(Python):
    """
    Forces a task to be performed using python 3.
    """

    def __init__(self, *args, **kwargs):
        """
        Create a python 3 task wrapper object.
        """
        super(Python, self).__init__(*args, **kwargs)

        self.setOption(
            'executableName',
            os.environ.get(
                'KOMBI_PYTHON3_EXECUTABLE',
                'python3'
            )
        )


# registering task wrappers
Subprocess.register(
    'python',
    Python
)

# also registering the subprocess
Subprocess.register(
    'subprocess',
    Python
)

# specific for python 2.x
Subprocess.register(
    'python2',
    _Python2
)

# specific for python 3.x
Subprocess.register(
    'python3',
    _Python3
)
