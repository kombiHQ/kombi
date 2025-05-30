import unittest
import os
import shutil
from ...BaseTestCase import BaseTestCase
from kombi.Task import Task
from kombi.Element.Fs import FsElement
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
        super().setUpClass()
        shutil.copy2(
            cls.__sourcePath,
            cls.__targetPath
        )

    def testChecksumTask(self):
        """
        Test that the checksum task works properly.
        """
        element = FsElement.createFromPath(self.__sourcePath)
        checksumTask = Task.create('checksum')
        checksumTask.add(element, self.__targetPath)
        result = checksumTask.output()
        self.assertEqual(len(result), 1)
        checksumTask = Task.create('checksum')
        checksumTask.add(element, self.__otherPath)
        self.assertRaises(ChecksumTaskMatchError, checksumTask.output)


if __name__ == "__main__":
    unittest.main()
