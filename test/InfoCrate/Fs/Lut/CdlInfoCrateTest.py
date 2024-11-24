import os
import unittest
from ....BaseTestCase import BaseTestCase
from kombi.InfoCrate.Fs import FsInfoCrate
from kombi.InfoCrate.PathHolder import PathHolder
from kombi.InfoCrate.Fs.Lut import CdlInfoCrate

class CdlInfoCrateTest(BaseTestCase):
    """Test Cdl infoCrate."""

    __cdlFile = os.path.join(BaseTestCase.dataTestsDirectory(), "test.cdl")

    def testCdlInfoCrate(self):
        """
        Test that the Cdl infoCrate test works properly.
        """
        infoCrate = FsInfoCrate.create(PathHolder(self.__cdlFile))
        self.assertIsInstance(infoCrate, CdlInfoCrate)

    def testCdlVariables(self):
        """
        Test that variables are set properly.
        """
        infoCrate = FsInfoCrate.create(PathHolder(self.__cdlFile))
        self.assertEqual(infoCrate.var("type"), "cdl")
        self.assertEqual(infoCrate.var("category"), "lut")
        self.assertEqual(infoCrate.var("slope"), [1.014, 1.0104, 0.62])
        self.assertEqual(infoCrate.var("offset"), [-0.00315, -0.00124, 0.3103])
        self.assertEqual(infoCrate.var("power"), [1.0, 0.9983, 1.0])
        self.assertEqual(infoCrate.var("saturation"), 1.09)


if __name__ == "__main__":
    unittest.main()
