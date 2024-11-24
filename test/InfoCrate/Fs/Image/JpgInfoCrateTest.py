import os
import unittest
from ....BaseTestCase import BaseTestCase
from kombi.InfoCrate import InfoCrate
from kombi.InfoCrate.PathHolder import PathHolder
from kombi.InfoCrate.Fs.Image import JpgInfoCrate

class JpgInfoCrateTest(BaseTestCase):
    """Test Jpg infoCrate."""

    __jpgFile = os.path.join(BaseTestCase.dataTestsDirectory(), "test.jpg")

    def testJpgInfoCrate(self):
        """
        Test that the Jpg infoCrate test works properly.
        """
        infoCrate = InfoCrate.create(PathHolder(self.__jpgFile))
        self.assertIsInstance(infoCrate, JpgInfoCrate)

    def testJpgVariables(self):
        """
        Test that variables are set properly.
        """
        infoCrate = InfoCrate.create(PathHolder(self.__jpgFile))
        self.assertEqual(infoCrate.var("type"), "jpg")
        self.assertEqual(infoCrate.var("category"), "image")
        self.assertEqual(infoCrate.var("imageType"), "single")
        self.assertEqual(infoCrate.var("width"), 512)
        self.assertEqual(infoCrate.var("height"), 512)


if __name__ == "__main__":
    unittest.main()
