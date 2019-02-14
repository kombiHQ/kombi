import unittest
import os
import distutils.spawn
from ..BaseTestCase import BaseTestCase
from chilopoda.Task import Task
from chilopoda.TaskWrapper import TaskWrapper
from chilopoda.Crawler.Fs import FsPath
from chilopoda.Resource import Resource

class Python2Test(BaseTestCase):
    """Test python 2 subprocess."""

    __sourcePath = os.path.join(BaseTestCase.dataTestsDirectory(), "test.exr")
    __taskPath = os.path.join(BaseTestCase.dataTestsDirectory(), "tasks", "PythonMajorVerTestTask.py")

    @unittest.skipIf(not distutils.spawn.find_executable(TaskWrapper.create('python2').option('executableName')), "python2 is not available on search path")
    def testPython2(self):
        """
        Test that the python3 subprocess works properly.
        """
        resource = Resource.get()
        resource.load(self.__taskPath)
        crawler = FsPath.createFromPath(self.__sourcePath)
        dummyTask = Task.create('pythonMajorVerTestTask')
        dummyTask.add(crawler)

        wrapper = TaskWrapper.create("python2")
        result = wrapper.run(dummyTask)
        self.assertTrue(len(result), 1)
        self.assertEqual(result[0].var("majorVer"), 2)


if __name__ == "__main__":
    unittest.main()
