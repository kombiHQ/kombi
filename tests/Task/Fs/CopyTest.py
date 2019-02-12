import unittest
import os
from ...BaseTestCase import BaseTestCase
from chilopoda.Task import Task
from chilopoda.Crawler.Fs import FsPath
from chilopoda.Crawler.Fs.Image import Exr

class CopyTest(BaseTestCase):
    """Test Copy task."""

    __sourcePath = os.path.join(BaseTestCase.dataDirectory(), "test.exr")
    __targetPath = os.path.join(BaseTestCase.tempDirectory(), "copyTest.exr")

    def testCopy(self):
        """
        Test that the copy task works properly.
        """
        crawler = FsPath.createFromPath(self.__sourcePath)
        copyTask = Task.create('copy')
        copyTask.add(crawler, self.__targetPath)
        result = copyTask.output()
        self.assertEqual(len(result), 1)
        crawler = result[0]
        self.assertEqual(crawler.var("filePath"), self.__targetPath)
        self.assertTrue(os.path.isfile(crawler.var("filePath")))
        self.assertIsInstance(crawler, Exr)
        self.assertEqual(crawler.var("width"), crawler.var("width"))
        self.assertEqual(crawler.var("height"), crawler.var("height"))

    @classmethod
    def tearDownClass(cls):
        """
        Remove the file that was copied.
        """
        os.remove(cls.__targetPath)


if __name__ == "__main__":
    unittest.main()
