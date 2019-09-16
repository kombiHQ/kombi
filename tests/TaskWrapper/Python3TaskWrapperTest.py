import unittest
import os
import distutils.spawn
from ..BaseTestCase import BaseTestCase
from kombi.Task import Task
from kombi.TaskWrapper import TaskWrapper
from kombi.Crawler.Fs import FsCrawler
from kombi.Resource import Resource

class Python3TaskWrapperTest(BaseTestCase):
    """Test python 3 test subprocess."""

    __sourcePath = os.path.join(BaseTestCase.dataTestsDirectory(), "test.exr")
    __taskPath = os.path.join(BaseTestCase.dataTestsDirectory(), "tasks", "PythonMajorVerTestTask.py")

    @unittest.skipIf(not distutils.spawn.find_executable(TaskWrapper.create('python3').option('executableName')), "python3 is not available on search path")
    def testPython3(self):
        """
        Test that the python3 subprocess works properly.
        """
        resource = Resource.get()
        resource.load(self.__taskPath)
        crawler = FsCrawler.createFromPath(self.__sourcePath)
        dummyTask = Task.create('pythonMajorVerTestTask')
        dummyTask.add(crawler)

        wrapper = TaskWrapper.create("python3")
        result = wrapper.run(dummyTask)
        self.assertTrue(len(result), 1)
        self.assertEqual(result[0].var("majorVer"), 3)


if __name__ == "__main__":
    unittest.main()
