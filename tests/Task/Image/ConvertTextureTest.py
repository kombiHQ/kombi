import os
import unittest
from ...BaseTestCase import BaseTestCase
from chilopoda.Task import Task
from chilopoda.Crawler.Fs import FsPath

class ConvertTextureTest(BaseTestCase):
    """
    Test ConvertTexture task.
    """

    __sourcePath = os.path.join(BaseTestCase.dataDirectory(), "test.png")
    __targetPath = os.path.join(BaseTestCase.tempDirectory(), "testToDelete.tx")

    def testConvertTexture(self):
        """
        Test that the ConvertTexture task works properly.
        """
        crawler = FsPath.createFromPath(self.__sourcePath)
        convertTask = Task.create('convertTexture')
        convertTask.setOption('maketxArgs', '-u --unpremult --oiio')
        convertTask.add(crawler, self.__targetPath)
        result = convertTask.output()

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].var('filePath'), self.__targetPath)
        self.assertTrue(os.path.exists(self.__targetPath))

    @classmethod
    def tearDownClass(cls):
        """
        Remove the file that was copied.
        """
        os.remove(cls.__targetPath)


if __name__ == "__main__":
    unittest.main()
