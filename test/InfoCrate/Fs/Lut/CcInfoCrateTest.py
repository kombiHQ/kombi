import os
import unittest
from ....BaseTestCase import BaseTestCase
from kombi.InfoCrate.Fs import FsInfoCrate
from kombi.InfoCrate.PathHolder import PathHolder
from kombi.InfoCrate.Fs.Lut import CcInfoCrate

class CcInfoCrateTest(BaseTestCase):
    """Test Cc infoCrate."""

    __ccFile = os.path.join(BaseTestCase.dataTestsDirectory(), "test.cc")

    def testCcInfoCrate(self):
        """
        Test that the Cc infoCrate test works properly.
        """
        infoCrate = FsInfoCrate.create(PathHolder(self.__ccFile))
        self.assertIsInstance(infoCrate, CcInfoCrate)

    def testCcVariables(self):
        """
        Test that variables are set properly.
        """
        infoCrate = FsInfoCrate.create(PathHolder(self.__ccFile))
        self.assertEqual(infoCrate.var("type"), "cc")
        self.assertEqual(infoCrate.var("category"), "lut")
        self.assertEqual(infoCrate.var("slope"), [1.2, 1.3, 1.4])
        self.assertEqual(infoCrate.var("offset"), [0.2, 0.3, 0.4])
        self.assertEqual(infoCrate.var("power"), [1.5, 1.6, 1.7])
        self.assertEqual(infoCrate.var("saturation"), 1.0)


if __name__ == "__main__":
    unittest.main()
