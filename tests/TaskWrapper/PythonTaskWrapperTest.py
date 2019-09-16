import unittest
import os
import OpenImageIO
from ..BaseTestCase import BaseTestCase
from kombi.Task import Task
from kombi.TaskWrapper import TaskWrapper
from kombi.Crawler.Fs import FsPathCrawler
from kombi.Resource import Resource

class PythonTaskWrapperTest(BaseTestCase):
    """Test python subprocess."""

    __sourcePath = os.path.join(BaseTestCase.dataTestsDirectory(), 'test.exr')
    __taskPath = os.path.join(BaseTestCase.dataTestsDirectory(), 'tasks', 'PythonTestTask.py')

    def testPythonMultiLevel(self):
        """
        Test that the Python subprocess works properly when launching it from another subprocess.
        """
        resource = Resource.get()
        resource.load(self.__taskPath)
        crawler = FsPathCrawler.createFromPath(self.__sourcePath)
        dummyTask = Task.create('pythonTestTask')
        dummyTask.add(crawler)
        dummyTask.setOption("runPython", True)
        wrapper = TaskWrapper.create('python')
        result = wrapper.run(dummyTask)
        self.assertTrue(len(result), 1)
        self.assertIn("testPython", result[0].varNames())
        self.assertEqual(result[0].var("testPython"), OpenImageIO.VERSION)

    def testPython(self):
        """
        Test that the Python subprocess works properly.
        """
        resource = Resource.get()
        resource.load(self.__taskPath)
        crawler = FsPathCrawler.createFromPath(self.__sourcePath)
        dummyTask = Task.create('pythonTestTask')
        dummyTask.add(crawler)
        dummyTask.setOption("runPython", False)
        wrapper = TaskWrapper.create('python')
        result = wrapper.run(dummyTask)
        self.assertTrue(len(result), 1)
        self.assertIn("testPython", result[0].varNames())
        self.assertEqual(result[0].var("testPython"), OpenImageIO.VERSION)


if __name__ == "__main__":
    unittest.main()
