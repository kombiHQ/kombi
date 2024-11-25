import sys
from kombi.Task import Task

class PythonMajorVerTestTask(Task):
    """
    Dummy task for testing python 3 subprocess.
    """

    def _perform(self):
        sourceElement = self.elements()[0]
        sourceElement.setVar("majorVer", sys.version_info[0])
        return [sourceElement.clone()]


Task.register(
    'pythonMajorVerTestTask',
    PythonMajorVerTestTask
)
