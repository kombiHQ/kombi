import os
import unittest
from ....BaseTestCase import BaseTestCase
from kombi.InfoCrate.Fs import FsInfoCrate
from kombi.InfoCrate.PathHolder import PathHolder
from kombi.InfoCrate.Fs.Lut import CccInfoCrate

class CccInfoCrateTest(BaseTestCase):
    """Test Ccc infoCrate."""

    __cccFile = os.path.join(BaseTestCase.dataTestsDirectory(), "test.ccc")

    def testCccInfoCrate(self):
        """
        Test that the Ccc infoCrate test works properly.
        """
        infoCrate = FsInfoCrate.create(PathHolder(self.__cccFile))
        self.assertIsInstance(infoCrate, CccInfoCrate)

    def testCccVariables(self):
        """
        Test that variables are set properly.
        """
        infoCrate = FsInfoCrate.create(PathHolder(self.__cccFile))
        self.assertEqual(infoCrate.var("type"), "ccc")
        self.assertEqual(infoCrate.var("category"), "lut")
        self.assertEqual(infoCrate.var("slope"), [1.1, 1.2, 1.3])
        self.assertEqual(infoCrate.var("offset"), [0.1, 0.2, 0.3])
        self.assertEqual(infoCrate.var("power"), [1.4, 1.5, 1.6])
        self.assertEqual(infoCrate.var("saturation"), 1.0)


if __name__ == "__main__":
    unittest.main()
