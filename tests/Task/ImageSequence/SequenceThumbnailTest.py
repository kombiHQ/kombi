import unittest
import os
import glob
from ...BaseTestCase import BaseTestCase
from chilopoda.Task import Task
from chilopoda.Crawler.Fs import FsPath

class SequenceThumbnailTest(BaseTestCase):
    """Test SequenceThumbnail task."""

    __sourcePath = os.path.join(BaseTestCase.dataDirectory(), "testSeq.*.exr")
    __testPath = os.path.join(BaseTestCase.dataDirectory(), "thumbnailSequence.jpg")
    __targetPath = os.path.join(BaseTestCase.tempDirectory(), "testToDelete.jpg")

    def testSequenceThumbnail(self):
        """
        Test that the SequenceThumbnail task works properly.
        """
        thumbnailTask = Task.create('sequenceThumbnail')
        sourceFiles = sorted(glob.glob(self.__sourcePath))
        for i in map(FsPath.createFromPath, sourceFiles):
            thumbnailTask.add(i, self.__targetPath)
        result = thumbnailTask.output()
        self.assertEqual(len(result), 1)
        crawler = result[0]
        self.assertEqual(crawler.var("width"), 640)
        self.assertEqual(crawler.var("height"), 360)
        checkTask = Task.create('checksum')
        checkTask.add(crawler, self.__testPath)
        checkTask.output()

    @classmethod
    def tearDownClass(cls):
        """
        Remove the file that was copied.
        """
        os.remove(cls.__targetPath)


if __name__ == "__main__":
    unittest.main()
