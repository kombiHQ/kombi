import unittest
import os
from ...BaseTestCase import BaseTestCase
from kombi.Task import Task
from kombi.Crawler.Fs import FsPath

class RemoveTest(BaseTestCase):
    """Test Remove task."""

    __path = os.path.join(BaseTestCase.tempDirectory(), "toRemove.exr")

    @classmethod
    def setUpClass(cls):
        """
        Create a file to remove in the test.
        """
        open(cls.__path, 'w').close()

    def testRemove(self):
        """
        Test that the remove task works properly.
        """
        crawler = FsPath.createFromPath(self.__path)
        removeTask = Task.create('remove')
        removeTask.add(crawler, self.__path)
        result = removeTask.output()
        self.assertEqual(len(result), 1)
        crawler = result[0]
        self.assertFalse(os.path.isfile(crawler.var("filePath")))


if __name__ == "__main__":
    unittest.main()
