import unittest
import os
from ...BaseTestCase import BaseTestCase
from kombi.Task import Task
from kombi.InfoCrate.Fs import FsInfoCrate
from kombi.InfoCrate.Fs.Image import ExrInfoCrate

class CopyTaskTest(BaseTestCase):
    """Test Copy task."""

    __sourcePath = os.path.join(BaseTestCase.dataTestsDirectory(), "test.exr")
    __targetPath = os.path.join(BaseTestCase.tempDirectory(), "copyTest.exr")

    def testCopy(self):
        """
        Test that the copy task works properly.
        """
        infoCrate = FsInfoCrate.createFromPath(self.__sourcePath)
        copyTask = Task.create('copy')
        copyTask.add(infoCrate, self.__targetPath)
        result = copyTask.output()
        self.assertEqual(len(result), 1)
        infoCrate = result[0]
        self.assertEqual(infoCrate.var("filePath"), self.__targetPath)
        self.assertTrue(os.path.isfile(infoCrate.var("filePath")))
        self.assertIsInstance(infoCrate, ExrInfoCrate)
        self.assertEqual(infoCrate.var("width"), infoCrate.var("width"))
        self.assertEqual(infoCrate.var("height"), infoCrate.var("height"))

    @classmethod
    def tearDownClass(cls):
        """
        Remove the file that was copied.
        """
        os.remove(cls.__targetPath)


if __name__ == "__main__":
    unittest.main()
