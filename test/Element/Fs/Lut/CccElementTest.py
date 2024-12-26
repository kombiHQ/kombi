import os
import unittest
from ....BaseTestCase import BaseTestCase
from kombi.Element.Fs import FsElement
from pathlib import Path
from kombi.Element.Fs.Lut import CccElement

class CccElementTest(BaseTestCase):
    """Test Ccc element."""

    __cccFile = os.path.join(BaseTestCase.dataTestsDirectory(), "test.ccc")

    def testCccElement(self):
        """
        Test that the Ccc element test works properly.
        """
        element = FsElement.create(Path(self.__cccFile))
        self.assertIsInstance(element, CccElement)

    def testCccVariables(self):
        """
        Test that variables are set properly.
        """
        element = FsElement.create(Path(self.__cccFile))
        self.assertEqual(element.var("type"), "ccc")
        self.assertEqual(element.var("category"), "lut")
        self.assertEqual(element.var("slope"), [1.1, 1.2, 1.3])
        self.assertEqual(element.var("offset"), [0.1, 0.2, 0.3])
        self.assertEqual(element.var("power"), [1.4, 1.5, 1.6])
        self.assertEqual(element.var("saturation"), 1.0)


if __name__ == "__main__":
    unittest.main()
