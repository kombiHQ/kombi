import os
import unittest
from ....BaseTestCase import BaseTestCase
from kombi.Element import Element
from pathlib import Path
from kombi.Element.Fs.Ascii import TxtElement

class TxtElementTest(BaseTestCase):
    """Test Txt element."""

    __txtFile = os.path.join(BaseTestCase.dataTestsDirectory(), "test.txt")

    def testTxtElement(self):
        """
        Test that the Txt element test works properly.
        """
        element = Element.create(Path(self.__txtFile))
        self.assertIsInstance(element, TxtElement)

    def testTxtVariables(self):
        """
        Test that variables are set properly.
        """
        element = Element.create(Path(self.__txtFile))
        self.assertEqual(element.var("type"), "txt")
        self.assertEqual(element.var("category"), "ascii")

    def testTxtContents(self):
        """
        Test that txt files are parsed properly.
        """
        element = Element.create(Path(self.__txtFile))
        testData = "testing txt file\nwith random data\n\n1 2 3\n"
        self.assertEqual(element.contents(), testData)


if __name__ == "__main__":
    unittest.main()
