import os
import sys
import shutil
import unittest
from ...BaseTestCase import BaseTestCase
from kombi.Task import Task
from kombi.Element.Fs import FsElement

class ChmodTaskTest(BaseTestCase):
    """Test Chmod task."""

    __dir = os.path.join(BaseTestCase.dataTestsDirectory(), "glob")
    __path = os.path.join(__dir, "images", "RND_ass_lookdev_default_beauty_tt.1001.exr")
    __targetPath = BaseTestCase.tempDirectory()

    @unittest.skipIf(sys.platform.startswith("win"), "not supported on windows")
    def testChmodFile(self):
        """
        Test that the chmod task works properly on a file.
        """
        chmodTestFile = os.path.join(self.__targetPath, 'chmodTestA.exr')
        shutil.copy(self.__path, chmodTestFile)
        element = FsElement.createFromPath(chmodTestFile)
        chmodTask = Task.create('chmod')
        chmodTask.add(element)
        for permission in ["644", "444", "744", "664"]:
            chmodTask.setOption('directoryMode', permission)
            chmodTask.setOption('fileMode', permission)
            result = chmodTask.output()
            self.assertEqual(len(result), 1)
            element = result[0]
            self.assertEqual(self.__getPermission(element.var('filePath')), permission)

    @unittest.skipIf(sys.platform.startswith("win"), "not supported on windows")
    def testChmodDir(self):
        """
        Test that the chmod task works properly on a directory.
        """
        element = FsElement.createFromPath(self.__targetPath)
        chmodTestFile = os.path.join(self.__targetPath, 'chmodTestB.exr')
        shutil.copy(self.__path, chmodTestFile)

        fileElement = FsElement.createFromPath(chmodTestFile)
        chmodTask = Task.create('chmod')
        chmodTask.add(element)
        chmodTask.add(fileElement)
        dirPerm = "775"
        filePerm = "664"
        chmodTask.setOption('directoryMode', dirPerm)
        chmodTask.setOption('fileMode', filePerm)
        result = chmodTask.output()
        self.assertEqual(len(result), 3)
        self.assertIn(self.__getPermission(self.__dir), [dirPerm, '755'])
        self.assertIn(self.__getPermission(self.__path), [filePerm, '644'])

    @unittest.skipIf(sys.platform.startswith("win"), "not supported on windows")
    def testSymlink(self):
        """
        Test that hardlinks are skipped when running the chmod task.
        """
        link = os.path.join(self.__targetPath, 'symlink.exr')
        os.symlink(self.__path, link)
        self.assertIn(self.__getPermission(link), ['664', '644'])
        self.assertTrue(os.path.islink(link))
        element = FsElement.createFromPath(link)
        chmodTask = Task.create('chmod')
        chmodTask.add(element)
        chmodTask.setOption('directoryMode', '775')
        chmodTask.setOption('fileMode', '775')
        chmodTask.output()
        self.assertIn(self.__getPermission(link), ['664', '644'])

    @staticmethod
    def __getPermission(filePath):
        return oct(os.stat(filePath).st_mode)[-3:]


if __name__ == "__main__":
    unittest.main()
