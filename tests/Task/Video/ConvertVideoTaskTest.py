import unittest
import os
from ...BaseTestCase import BaseTestCase
from kombi.Task import Task
from kombi.Crawler.Fs import FsPathCrawler

class ConvertVideoTaskTest(BaseTestCase):
    """Test ConvertVideo task."""

    __sourcePath = os.path.join(BaseTestCase.dataTestsDirectory(), "videoNoTimeCode.mov")
    __targetPath = os.path.join(BaseTestCase.tempDirectory(), "testToDelete.mov")

    def testConvertVideo(self):
        """
        Test that the Convert Video task works properly.
        """
        crawler = FsPathCrawler.createFromPath(self.__sourcePath)
        convertTask = Task.create('convertVideo')
        convertTask.add(crawler, self.__targetPath)
        result = convertTask.output()
        self.assertEqual(len(result), 1)

        # the check is currently done through an approximation
        # from the expected size rather than a hash due metadata
        # that can vary the file size
        convertedSize = os.path.getsize(result[0].var('filePath'))
        self.assertGreaterEqual(convertedSize, 1450000)
        self.assertLessEqual(convertedSize, 1600000)

    @classmethod
    def tearDownClass(cls):
        """
        Remove the file that was converted.
        """
        os.remove(cls.__targetPath)


if __name__ == "__main__":
    unittest.main()
