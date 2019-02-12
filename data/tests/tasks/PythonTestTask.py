from chilopoda.Task import Task
from chilopoda.TaskWrapper import TaskWrapper

class PythonTestTask(Task):
    """
    Dummy task for testing Python subprocess.
    """

    def _perform(self):
        sourceCrawler = self.crawlers()[0]
        if self.option('runPython'):
            dummyTask = Task.create('pythonTestTask')
            dummyTask.setOption("runPython", False)
            dummyTask.add(sourceCrawler)
            wrapper = TaskWrapper.create('python')
            result = wrapper.run(dummyTask)
        else:
            import OpenImageIO
            sourceCrawler.setVar("testPython", OpenImageIO.VERSION)
            result = [sourceCrawler.clone()]

        return result


Task.register(
    'pythonTestTask',
    PythonTestTask
)
