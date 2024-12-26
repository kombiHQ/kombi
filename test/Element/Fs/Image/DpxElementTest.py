import os
import unittest
from ....BaseTestCase import BaseTestCase
from kombi.Element import Element
from pathlib import Path
from kombi.Element.Fs.Image import DpxElement

class DpxElementTest(BaseTestCase):
    """Test Dpx element."""

    __dpxFile = os.path.join(BaseTestCase.dataTestsDirectory(), "test.dpx")

    def testDpxElement(self):
        """
        Test that the Dpx element test works properly.
        """
        element = Element.create(Path(self.__dpxFile))
        self.assertIsInstance(element, DpxElement)

    def testDpxVariables(self):
        """
        Test that variables are set properly.
        """
        element = Element.create(Path(self.__dpxFile))
        self.assertEqual(element.var("type"), "dpx")
        self.assertEqual(element.var("category"), "image")
        self.assertEqual(element.var("imageType"), "single")
        self.assertEqual(element.var("width"), 1920)
        self.assertEqual(element.var("height"), 1080)


if __name__ == "__main__":
    unittest.main()
