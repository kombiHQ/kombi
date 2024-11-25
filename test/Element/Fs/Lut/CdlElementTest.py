import os
import unittest
from ....BaseTestCase import BaseTestCase
from kombi.Element.Fs import FsElement
from kombi.Element.PathHolder import PathHolder
from kombi.Element.Fs.Lut import CdlElement

class CdlElementTest(BaseTestCase):
    """Test Cdl element."""

    __cdlFile = os.path.join(BaseTestCase.dataTestsDirectory(), "test.cdl")

    def testCdlElement(self):
        """
        Test that the Cdl element test works properly.
        """
        element = FsElement.create(PathHolder(self.__cdlFile))
        self.assertIsInstance(element, CdlElement)

    def testCdlVariables(self):
        """
        Test that variables are set properly.
        """
        element = FsElement.create(PathHolder(self.__cdlFile))
        self.assertEqual(element.var("type"), "cdl")
        self.assertEqual(element.var("category"), "lut")
        self.assertEqual(element.var("slope"), [1.014, 1.0104, 0.62])
        self.assertEqual(element.var("offset"), [-0.00315, -0.00124, 0.3103])
        self.assertEqual(element.var("power"), [1.0, 0.9983, 1.0])
        self.assertEqual(element.var("saturation"), 1.09)


if __name__ == "__main__":
    unittest.main()
