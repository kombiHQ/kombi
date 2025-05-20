import unittest
import os
from ...BaseTestCase import BaseTestCase
from kombi.Task import Task
from kombi.Element.Fs import FsElement
from kombi.Element.Fs.Image import ExrElement

class CopyTaskTest(BaseTestCase):
    """Test Copy task."""

    __sourcePath = os.path.join(BaseTestCase.dataTestsDirectory(), "test.exr")
    __targetPath = os.path.join(BaseTestCase.tempDirectory(), "copyTest.exr")

    def testCopy(self):
        """
        Test that the copy task works properly.
        """
        element = FsElement.createFromPath(self.__sourcePath)
        copyTask = Task.create('copy')
        copyTask.add(element, self.__targetPath)
        result = copyTask.output()
        self.assertEqual(len(result), 1)
        element = result[0]
        self.assertEqual(element.var("filePath"), self.__targetPath)
        self.assertTrue(os.path.isfile(element.var("filePath")))
        self.assertIsInstance(element, ExrElement)
        self.assertEqual(element.var("width"), element.var("width"))
        self.assertEqual(element.var("height"), element.var("height"))


if __name__ == "__main__":
    unittest.main()
