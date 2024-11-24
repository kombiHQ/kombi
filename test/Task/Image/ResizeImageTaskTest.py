import unittest
import os
from ...BaseTestCase import BaseTestCase
from kombi.Task import Task
from kombi.InfoCrate.Fs import FsInfoCrate

class ResizeImageTaskTest(BaseTestCase):
    """Test ResizeImage task."""

    __sourcePath = os.path.join(BaseTestCase.dataTestsDirectory(), "testSeq.0001.exr")
    __targetPath = os.path.join(BaseTestCase.tempDirectory(), "testToDelete.jpg")

    def testResizeImage(self):
        """
        Test that the ResizeImage task works properly.
        """
        infoCrate = FsInfoCrate.createFromPath(self.__sourcePath)
        resizeTask = Task.create('resizeImage')
        resizeTask.add(infoCrate, self.__targetPath)
        resizeTask.setOption("width", "480")
        resizeTask.setOption("height", "270")
        for convertToRGBA in [False, True]:
            resizeTask.setOption("convertToRGBA", convertToRGBA)
            result = resizeTask.output()
            self.assertEqual(len(result), 1)
            infoCrate = result[0]
            self.assertEqual(infoCrate.var("width"), 480)
            self.assertEqual(infoCrate.var("height"), 270)

    @classmethod
    def tearDownClass(cls):
        """
        Remove the file that was copied.
        """
        os.remove(cls.__targetPath)


if __name__ == "__main__":
    unittest.main()
