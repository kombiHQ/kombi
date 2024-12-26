import os
import unittest
from ....BaseTestCase import BaseTestCase
from kombi.Element import Element
from pathlib import Path
from kombi.Element.Fs.Texture import TextureElement

class TextureElementTest(BaseTestCase):
    """Test Texture element."""

    __exrFile = os.path.join(BaseTestCase.dataTestsDirectory(), "test_DIFF_u1_v1.exr")
    __tifFile = os.path.join(BaseTestCase.dataTestsDirectory(), "test_bump_1002.tif")
    __badExrFile = os.path.join(BaseTestCase.dataTestsDirectory(), "test_0001.exr")

    def testTextureElement(self):
        """
        Test that the Texture element test works properly.
        """
        element = Element.registeredType('texture')(Path(self.__exrFile))
        self.assertIsInstance(element, TextureElement)
        element = Element.registeredType('texture')(Path(self.__tifFile))
        self.assertIsInstance(element, TextureElement)
        self.assertFalse(Element.registeredType('texture').test(Path(self.__badExrFile), None, enable=True))

    def testTextureVariables(self):
        """
        Test that variables are set properly.
        """
        element = Element.registeredType('texture')(Path(self.__exrFile))
        self.assertTrue(element.test(element.path(), None, enable=True))
        self.assertEqual(element.var("category"), "texture")
        self.assertEqual(element.var("assetName"), "test")
        self.assertEqual(element.var("mapType"), "DIFF")
        self.assertEqual(element.var("udim"), 1001)
        self.assertEqual(element.var("variant"), "default")

        element = Element.registeredType('texture')(Path(self.__tifFile))
        self.assertTrue(element.test(element.path(), None, enable=True))
        self.assertEqual(element.var("assetName"), "test")
        self.assertEqual(element.var("mapType"), "BUMP")
        self.assertEqual(element.var("udim"), 1002)
        self.assertEqual(element.var("variant"), "default")

    def testTextureTags(self):
        """
        Test that the tags are set properly.
        """
        element = Element.registeredType('texture')(Path(self.__exrFile))
        self.assertEqual(element.tag("group"), "test-default")


if __name__ == "__main__":
    unittest.main()
