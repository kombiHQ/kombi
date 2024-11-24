import os
import unittest
from ...BaseTestCase import BaseTestCase
from kombi.InfoCrate import InfoCrate
from kombi.InfoCrate.PathHolder import PathHolder
from kombi.InfoCrate.Fs import DirectoryInfoCrate

class DirectoryInfoCrateTest(BaseTestCase):
    """Test Directory infoCrate."""

    __dir = os.path.join(BaseTestCase.dataTestsDirectory(), "640x480")

    def testDirectoryInfoCrate(self):
        """
        Test that the Directory infoCrate test works properly.
        """
        infoCrate = InfoCrate.create(PathHolder(self.__dir))
        self.assertIsInstance(infoCrate, DirectoryInfoCrate)

    def testDirectoryVariables(self):
        """
        Test that the variables are set properly.
        """
        infoCrate = InfoCrate.create(PathHolder(self.__dir))
        self.assertEqual(infoCrate.var("width"), 640)
        self.assertEqual(infoCrate.var("height"), 480)

    def testIsLeaf(self):
        """
        Test to show directory infoCrate is not a leaf.
        """
        infoCrate = InfoCrate.create(PathHolder(self.__dir))
        self.assertFalse(infoCrate.isLeaf())

    def testBadFile(self):
        """
        Test to show that file names with illegal characters are skipped.
        """
        infoCrate = InfoCrate.create(PathHolder(self.dataTestsDirectory()))
        infoCratePaths = map(lambda x: x.var("filePath"), infoCrate.children())
        self.assertNotIn(os.path.join(self.__dir, "bad file.txt"), infoCratePaths)


if __name__ == "__main__":
    unittest.main()
