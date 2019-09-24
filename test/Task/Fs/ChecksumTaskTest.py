import unittest
import os
import shutil
from ...BaseTestCase import BaseTestCase
from kombi.Task import Task
from kombi.Crawler.Fs import FsCrawler
from kombi.Task.Fs.ChecksumTask import ChecksumTaskMatchError

class ChecksumTaskTest(BaseTestCase):
    """Test Checksum task."""

    __sourcePath = os.path.join(BaseTestCase.dataTestsDirectory(), "test.exr")
    __targetPath = os.path.join(BaseTestCase.tempDirectory(), "testCopy.exr")
    __otherPath = os.path.join(BaseTestCase.dataTestsDirectory(), "RND_ass_lookdev_default_beauty_tt.1001.exr")

    @classmethod
    def setUpClass(cls):
        """
        Create copy of the source file.
        """
        shutil.copy2(
            cls.__sourcePath,
            cls.__targetPath
        )

    def testChecksumTask(self):
        """
        Test that the checksum task works properly.
        """
        crawler = FsCrawler.createFromPath(self.__sourcePath)
        checksumTask = Task.create('checksum')
        checksumTask.add(crawler, self.__targetPath)
        result = checksumTask.output()
        self.assertEqual(len(result), 1)
        checksumTask = Task.create('checksum')
        checksumTask.add(crawler, self.__otherPath)
        self.assertRaises(ChecksumTaskMatchError, checksumTask.output)

    @classmethod
    def tearDownClass(cls):
        """
        Remove the file that was copied.
        """
        os.remove(cls.__targetPath)


if __name__ == "__main__":
    unittest.main()
