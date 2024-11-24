import os
import unittest
from ....BaseTestCase import BaseTestCase
from kombi.InfoCrate import InfoCrate
from kombi.InfoCrate.PathHolder import PathHolder
from kombi.InfoCrate.Fs.Image import PngInfoCrate

class PngInfoCrateTest(BaseTestCase):
    """Test Exr infoCrate."""

    __pngFile = os.path.join(BaseTestCase.dataTestsDirectory(), "test.png")

    def testPngInfoCrate(self):
        """
        Test that the Png infoCrate test works properly.
        """
        infoCrate = InfoCrate.create(PathHolder(self.__pngFile))
        self.assertIsInstance(infoCrate, PngInfoCrate)

    def testPngVariables(self):
        """
        Test that variables are set properly.
        """
        infoCrate = InfoCrate.create(PathHolder(self.__pngFile))
        self.assertEqual(infoCrate.var("type"), "png")
        self.assertEqual(infoCrate.var("category"), "image")
        self.assertEqual(infoCrate.var("imageType"), "single")
        # Current version of Oiio doesn't work with png.
        # Skipping this test for now.
        # self.assertEqual(infoCrate.var("width"), 640)
        # self.assertEqual(infoCrate.var("height"), 480)


if __name__ == "__main__":
    unittest.main()
