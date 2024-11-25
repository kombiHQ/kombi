import os
import unittest
from ....BaseTestCase import BaseTestCase
from kombi.Element import Element
from kombi.Element.PathHolder import PathHolder
from kombi.Element.Fs.Image import PngElement

class PngElementTest(BaseTestCase):
    """Test Exr element."""

    __pngFile = os.path.join(BaseTestCase.dataTestsDirectory(), "test.png")

    def testPngElement(self):
        """
        Test that the Png element test works properly.
        """
        element = Element.create(PathHolder(self.__pngFile))
        self.assertIsInstance(element, PngElement)

    def testPngVariables(self):
        """
        Test that variables are set properly.
        """
        element = Element.create(PathHolder(self.__pngFile))
        self.assertEqual(element.var("type"), "png")
        self.assertEqual(element.var("category"), "image")
        self.assertEqual(element.var("imageType"), "single")
        # Current version of Oiio doesn't work with png.
        # Skipping this test for now.
        # self.assertEqual(element.var("width"), 640)
        # self.assertEqual(element.var("height"), 480)


if __name__ == "__main__":
    unittest.main()
