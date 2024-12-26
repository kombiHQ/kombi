import os
import unittest
from ....BaseTestCase import BaseTestCase
from kombi.Element import Element
from pathlib import Path
from kombi.Element.Fs.Image import JpgElement

class JpgElementTest(BaseTestCase):
    """Test Jpg element."""

    __jpgFile = os.path.join(BaseTestCase.dataTestsDirectory(), "test.jpg")

    def testJpgElement(self):
        """
        Test that the Jpg element test works properly.
        """
        element = Element.create(Path(self.__jpgFile))
        self.assertIsInstance(element, JpgElement)

    def testJpgVariables(self):
        """
        Test that variables are set properly.
        """
        element = Element.create(Path(self.__jpgFile))
        self.assertEqual(element.var("type"), "jpg")
        self.assertEqual(element.var("category"), "image")
        self.assertEqual(element.var("imageType"), "single")
        self.assertEqual(element.var("width"), 512)
        self.assertEqual(element.var("height"), 512)


if __name__ == "__main__":
    unittest.main()
