import os
import unittest
from ....BaseTestCase import BaseTestCase
from kombi.Element.Fs import FsElement
from pathlib import Path
from kombi.Element.Fs.Lut import CcElement

class CcElementTest(BaseTestCase):
    """Test Cc element."""

    __ccFile = os.path.join(BaseTestCase.dataTestsDirectory(), "test.cc")

    def testCcElement(self):
        """
        Test that the Cc element test works properly.
        """
        element = FsElement.create(Path(self.__ccFile))
        self.assertIsInstance(element, CcElement)

    def testCcVariables(self):
        """
        Test that variables are set properly.
        """
        element = FsElement.create(Path(self.__ccFile))
        self.assertEqual(element.var("type"), "cc")
        self.assertEqual(element.var("category"), "lut")
        self.assertEqual(element.var("slope"), [1.2, 1.3, 1.4])
        self.assertEqual(element.var("offset"), [0.2, 0.3, 0.4])
        self.assertEqual(element.var("power"), [1.5, 1.6, 1.7])
        self.assertEqual(element.var("saturation"), 1.0)


if __name__ == "__main__":
    unittest.main()
