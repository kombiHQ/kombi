import unittest
import os
from ...BaseTestCase import BaseTestCase
from kombi.Task import Task
from kombi.Element.Fs import FsElement

class ResizeImageTaskTest(BaseTestCase):
    """Test ResizeImage task."""

    __sourcePath = os.path.join(BaseTestCase.dataTestsDirectory(), "testSeq.0001.exr")
    __targetPath = os.path.join(BaseTestCase.tempDirectory(), "testToDelete.jpg")

    def testResizeImage(self):
        """
        Test that the ResizeImage task works properly.
        """
        element = FsElement.createFromPath(self.__sourcePath)
        resizeTask = Task.create('resizeImage')
        resizeTask.add(element, self.__targetPath)
        resizeTask.setOption("width", "480")
        resizeTask.setOption("height", "270")
        for convertToRGBA in [False, True]:
            resizeTask.setOption("convertToRGBA", convertToRGBA)
            result = resizeTask.output()
            self.assertEqual(len(result), 1)
            element = result[0]
            self.assertEqual(element.var("width"), 480)
            self.assertEqual(element.var("height"), 270)


if __name__ == "__main__":
    unittest.main()
