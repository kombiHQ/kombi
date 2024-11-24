import sys
from kombi.Task import Task

class PythonMajorVerTestTask(Task):
    """
    Dummy task for testing python 3 subprocess.
    """

    def _perform(self):
        sourceInfoCrate = self.infoCrates()[0]
        sourceInfoCrate.setVar("majorVer", sys.version_info[0])
        return [sourceInfoCrate.clone()]


Task.register(
    'pythonMajorVerTestTask',
    PythonMajorVerTestTask
)
