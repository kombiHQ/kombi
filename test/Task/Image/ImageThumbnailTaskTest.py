import unittest
import os
from ...BaseTestCase import BaseTestCase
from kombi.Task import Task
from kombi.InfoCrate.Fs import FsInfoCrate

class ImageThumbnailTaskTest(BaseTestCase):
    """Test ImageThumbnail task."""

    __sourcePath = os.path.join(BaseTestCase.dataTestsDirectory(), "test.dpx")
    __targetPath = os.path.join(BaseTestCase.tempDirectory(), "testToDelete.jpg")

    def testImageThumbnail(self):
        """
        Test that the ImageThumbnail task works properly.
        """
        infoCrate = FsInfoCrate.createFromPath(self.__sourcePath)
        thumbnailTask = Task.create('imageThumbnail')
        thumbnailTask.add(infoCrate, self.__targetPath)
        result = thumbnailTask.output()
        self.assertEqual(len(result), 1)
        infoCrate = result[0]
        self.assertEqual(infoCrate.var("width"), 640)
        self.assertEqual(infoCrate.var("height"), 360)

    @classmethod
    def tearDownClass(cls):
        """
        Remove the file that was copied.
        """
        os.remove(cls.__targetPath)


if __name__ == "__main__":
    unittest.main()
