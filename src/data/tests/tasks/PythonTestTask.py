from kombi.Task import Task
from kombi.TaskWrapper import TaskWrapper

class PythonTestTask(Task):
    """
    Dummy task for testing Python subprocess.
    """

    def _perform(self):
        sourceInfoCrate = self.infoCrates()[0]
        if self.option('runPython'):
            dummyTask = Task.create('pythonTestTask')
            dummyTask.setOption("runPython", False)
            dummyTask.add(sourceInfoCrate)
            wrapper = TaskWrapper.create('python')
            result = wrapper.run(dummyTask)
        else:
            import OpenImageIO
            sourceInfoCrate.setVar("testPython", OpenImageIO.VERSION)
            result = [sourceInfoCrate.clone()]

        return result


Task.register(
    'pythonTestTask',
    PythonTestTask
)
