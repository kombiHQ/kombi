import os
import unittest
from ....BaseTestCase import BaseTestCase
from kombi.InfoCrate import InfoCrate
from kombi.InfoCrate.PathHolder import PathHolder
from kombi.InfoCrate.Fs.Image import DpxInfoCrate

class DpxInfoCrateTest(BaseTestCase):
    """Test Dpx infoCrate."""

    __dpxFile = os.path.join(BaseTestCase.dataTestsDirectory(), "test.dpx")

    def testDpxInfoCrate(self):
        """
        Test that the Dpx infoCrate test works properly.
        """
        infoCrate = InfoCrate.create(PathHolder(self.__dpxFile))
        self.assertIsInstance(infoCrate, DpxInfoCrate)

    def testDpxVariables(self):
        """
        Test that variables are set properly.
        """
        infoCrate = InfoCrate.create(PathHolder(self.__dpxFile))
        self.assertEqual(infoCrate.var("type"), "dpx")
        self.assertEqual(infoCrate.var("category"), "image")
        self.assertEqual(infoCrate.var("imageType"), "single")
        self.assertEqual(infoCrate.var("width"), 1920)
        self.assertEqual(infoCrate.var("height"), 1080)


if __name__ == "__main__":
    unittest.main()
