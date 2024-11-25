from kombi.Task import Task
from kombi.TaskWrapper import TaskWrapper

class PythonTestTask(Task):
    """
    Dummy task for testing Python subprocess.
    """

    def _perform(self):
        sourceElement = self.elements()[0]
        if self.option('runPython'):
            dummyTask = Task.create('pythonTestTask')
            dummyTask.setOption("runPython", False)
            dummyTask.add(sourceElement)
            wrapper = TaskWrapper.create('python')
            result = wrapper.run(dummyTask)
        else:
            import OpenImageIO
            sourceElement.setVar("testPython", OpenImageIO.VERSION)
            result = [sourceElement.clone()]

        return result


Task.register(
    'pythonTestTask',
    PythonTestTask
)
