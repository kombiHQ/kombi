import unittest
import os
import distutils.spawn
from ..BaseTestCase import BaseTestCase
from chilopoda.Task import Task
from chilopoda.TaskWrapper import TaskWrapper
from chilopoda.Crawler.Fs import FsPath
from chilopoda.Resource import Resource

class Python3Test(BaseTestCase):
    """Test python 3 test subprocess."""

    __sourcePath = os.path.join(BaseTestCase.dataDirectory(), "test.exr")
    __taskPath = os.path.join(BaseTestCase.dataDirectory(), "tasks", "PythonMajorVerTestTask.py")

    @unittest.skipIf(not distutils.spawn.find_executable(TaskWrapper.create('python3').option('executableName')), "python3 is not available on search path")
    def testPython3(self):
        """
        Test that the python3 subprocess works properly.
        """
        resource = Resource.get()
        resource.load(self.__taskPath)
        crawler = FsPath.createFromPath(self.__sourcePath)
        dummyTask = Task.create('pythonMajorVerTestTask')
        dummyTask.add(crawler)

        wrapper = TaskWrapper.create("python3")
        result = wrapper.run(dummyTask)
        self.assertTrue(len(result), 1)
        self.assertEqual(result[0].var("majorVer"), 3)


if __name__ == "__main__":
    unittest.main()