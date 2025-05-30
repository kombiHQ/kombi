import unittest
import os
from ..BaseTestCase import BaseTestCase
from kombi.Task import Task
from kombi.TaskWrapper import TaskWrapper
from kombi.Element.Fs import FsElement
from kombi.ResourceLoader import ResourceLoader

class Python3TaskWrapperTest(BaseTestCase):
    """Test python 3 test subprocess."""

    __sourcePath = os.path.join(BaseTestCase.dataTestsDirectory(), "test.exr")
    __taskPath = os.path.join(BaseTestCase.dataTestsDirectory(), "tasks", "PythonMajorVerTestTask.py")

    def testPython3(self):
        """
        Test that the python3 subprocess works properly.
        """
        resource = ResourceLoader.get()
        resource.load(self.__taskPath)
        element = FsElement.createFromPath(self.__sourcePath)
        dummyTask = Task.create('pythonMajorVerTestTask')
        dummyTask.add(element)

        wrapper = TaskWrapper.create("python3")
        result = wrapper.run(dummyTask)
        self.assertTrue(len(result), 1)
        self.assertEqual(result[0].var("majorVer"), 3)


if __name__ == "__main__":
    unittest.main()
