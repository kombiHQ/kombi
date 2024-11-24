import unittest
import os
import sys
from ...BaseTestCase import BaseTestCase
from kombi.Task import Task
from kombi.InfoCrate.Fs import FsInfoCrate

class ChmodTaskTest(BaseTestCase):
    """Test Chmod task."""

    __dir = os.path.join(BaseTestCase.dataTestsDirectory(), "glob")
    __path = os.path.join(__dir, "images", "RND_ass_lookdev_default_beauty_tt.1001.exr")

    @unittest.skipIf(sys.platform.startswith("win"), "not supported on windows")
    def testChmodFile(self):
        """
        Test that the chmod task works properly on a file.
        """
        infoCrate = FsInfoCrate.createFromPath(self.__path)
        chmodTask = Task.create('chmod')
        chmodTask.add(infoCrate, self.__path)
        for permission in ["644", "444", "744", "664"]:
            chmodTask.setOption('directoryMode', permission)
            chmodTask.setOption('fileMode', permission)
            result = chmodTask.output()
            self.assertEqual(len(result), 1)
            infoCrate = result[0]
            self.assertEqual(self.__getPermission(infoCrate.var('filePath')), permission)

    @unittest.skipIf(sys.platform.startswith("win"), "not supported on windows")
    def testChmodDir(self):
        """
        Test that the chmod task works properly on a directory.
        """
        infoCrate = FsInfoCrate.createFromPath(self.__dir)
        fileInfoCrate = FsInfoCrate.createFromPath(self.__path)
        chmodTask = Task.create('chmod')
        chmodTask.add(infoCrate, self.__dir)
        chmodTask.add(fileInfoCrate, self.__dir)
        dirPerm = "775"
        filePerm = "664"
        chmodTask.setOption('directoryMode', dirPerm)
        chmodTask.setOption('fileMode', filePerm)
        result = chmodTask.output()
        self.assertEqual(len(result), 1)
        self.assertEqual(self.__getPermission(self.__dir), dirPerm)
        self.assertEqual(self.__getPermission(self.__path), filePerm)

    @unittest.skipIf(sys.platform.startswith("win"), "not supported on windows")
    def testSymlink(self):
        """
        Test that hardlinks are skipped when running the chmod task.
        """
        link = os.path.join(self.dataTestsDirectory(), 'symlink.exr')
        os.symlink(self.__path, link)
        self.assertEqual(self.__getPermission(link), '664')
        self.assertTrue(os.path.islink(link))
        infoCrate = FsInfoCrate.createFromPath(link)
        chmodTask = Task.create('chmod')
        chmodTask.add(infoCrate, link)
        chmodTask.setOption('directoryMode', '775')
        chmodTask.setOption('fileMode', '775')
        chmodTask.output()
        self.assertEqual(self.__getPermission(link), '664')
        self.addCleanup(self.cleanup, link)

    def cleanup(self, fileToDelete):
        """
        Remove file created during test.
        """
        os.remove(fileToDelete)

    @staticmethod
    def __getPermission(filePath):
        return oct(os.stat(filePath).st_mode)[-3:]


if __name__ == "__main__":
    unittest.main()
