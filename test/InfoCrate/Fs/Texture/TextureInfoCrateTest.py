import os
import unittest
from ....BaseTestCase import BaseTestCase
from kombi.InfoCrate import InfoCrate
from kombi.InfoCrate.PathHolder import PathHolder
from kombi.InfoCrate.Fs.Texture import TextureInfoCrate

class TextureInfoCrateTest(BaseTestCase):
    """Test Texture infoCrate."""

    __exrFile = os.path.join(BaseTestCase.dataTestsDirectory(), "test_DIFF_u1_v1.exr")
    __tifFile = os.path.join(BaseTestCase.dataTestsDirectory(), "test_bump_1002.tif")
    __badExrFile = os.path.join(BaseTestCase.dataTestsDirectory(), "test_0001.exr")

    def testTextureInfoCrate(self):
        """
        Test that the Texture infoCrate test works properly.
        """
        infoCrate = InfoCrate.registeredType('texture')(PathHolder(self.__exrFile))
        self.assertIsInstance(infoCrate, TextureInfoCrate)
        infoCrate = InfoCrate.registeredType('texture')(PathHolder(self.__tifFile))
        self.assertIsInstance(infoCrate, TextureInfoCrate)
        self.assertFalse(InfoCrate.registeredType('texture').test(PathHolder(self.__badExrFile), None, enable=True))

    def testTextureVariables(self):
        """
        Test that variables are set properly.
        """
        infoCrate = InfoCrate.registeredType('texture')(PathHolder(self.__exrFile))
        self.assertTrue(infoCrate.test(infoCrate.pathHolder(), None, enable=True))
        self.assertEqual(infoCrate.var("category"), "texture")
        self.assertEqual(infoCrate.var("assetName"), "test")
        self.assertEqual(infoCrate.var("mapType"), "DIFF")
        self.assertEqual(infoCrate.var("udim"), 1001)
        self.assertEqual(infoCrate.var("variant"), "default")

        infoCrate = InfoCrate.registeredType('texture')(PathHolder(self.__tifFile))
        self.assertTrue(infoCrate.test(infoCrate.pathHolder(), None, enable=True))
        self.assertEqual(infoCrate.var("assetName"), "test")
        self.assertEqual(infoCrate.var("mapType"), "BUMP")
        self.assertEqual(infoCrate.var("udim"), 1002)
        self.assertEqual(infoCrate.var("variant"), "default")

    def testTextureTags(self):
        """
        Test that the tags are set properly.
        """
        infoCrate = InfoCrate.registeredType('texture')(PathHolder(self.__exrFile))
        self.assertEqual(infoCrate.tag("group"), "test-default")


if __name__ == "__main__":
    unittest.main()
