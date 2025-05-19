import os
import sys
import shutil
import unittest
import platform
from ...BaseTestCase import BaseTestCase
from kombi.Task import Task
from kombi.Element.Fs import FsElement

class LinkTaskTest(BaseTestCase):
    """
    Test link task.
    """
    __sourcePath = os.path.join(BaseTestCase.dataTestsDirectory(), "test.exr")
    __targetPath = os.path.join(BaseTestCase.tempDirectory(), "test.exr")
    __targetSymlinkPath = os.path.join(BaseTestCase.tempDirectory(), "test_symlink.exr")
    __targetHardlinkPath = os.path.join(BaseTestCase.tempDirectory(), "test_hardlink.exr")

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

    def testSymlink(self):
        """
        Test that symlink support in link task works properly.
        """
        element = FsElement.createFromPath(self.__targetPath)

        linkTask = Task.create('link')
        linkTask.setOption('type', 'symlink')
        linkTask.add(element, self.__targetSymlinkPath)

        result = None
        try:
            result = linkTask.output()
        except OSError as err:
            if str(err).startswith('[WinError 1314]'):
                sys.stderr.write('Current user has no privilege for creating symlinks')

        if result is None:
            return

        self.assertEqual(len(result), 1)
        self.assertTrue(os.path.exists(result[0].var('filePath')))

        if not platform.system() == "Windows":
            self.assertTrue(os.path.islink(result[0].var('filePath')))

    def testHardlink(self):
        """
        Test that hardlink support in link task works properly.
        """
        element = FsElement.createFromPath(self.__targetPath)

        linkTask = Task.create('link')
        linkTask.setOption('type', 'hardlink')
        linkTask.add(element, self.__targetHardlinkPath)
        result = linkTask.output()
        self.assertEqual(len(result), 1)
        self.assertTrue(os.path.exists(result[0].var('filePath')))
        self.assertFalse(os.path.islink(result[0].var('filePath')))


if __name__ == "__main__":
    unittest.main()
