import sys
from kombi.Task import Task

class PythonMajorVerTestTask(Task):
    """
    Dummy task for testing python 3 subprocess.
    """

    def _perform(self):
        sourceCrawler = self.crawlers()[0]
        sourceCrawler.setVar("majorVer", sys.version_info[0])
        return [sourceCrawler.clone()]


Task.register(
    'pythonMajorVerTestTask',
    PythonMajorVerTestTask
)
