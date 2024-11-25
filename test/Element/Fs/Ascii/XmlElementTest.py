import os
import unittest
from ....BaseTestCase import BaseTestCase
from kombi.Element.Fs import FsElement
from kombi.Element.Fs.Ascii import XmlElement

class XmlElementTest(BaseTestCase):
    """Test Xml element."""

    __xmlFile = os.path.join(BaseTestCase.dataTestsDirectory(), "test.xml")

    def testXmlElement(self):
        """
        Test that the Xml element test works properly.
        """
        element = FsElement.createFromPath(self.__xmlFile)
        self.assertIsInstance(element, XmlElement)

    def testXmlVariables(self):
        """
        Test that variables are set properly.
        """
        element = FsElement.createFromPath(self.__xmlFile)
        self.assertEqual(element.var("type"), "xml")
        self.assertEqual(element.var("category"), "ascii")

    def testXmlContents(self):
        """
        Test that txt files are parsed properly.
        """
        element = FsElement.createFromPath(self.__xmlFile)
        self.assertEqual(element.queryTag('testC')[0], "testing child C")
        self.assertEqual(element.queryTag('testD1')[0], "1 2 3")
        self.assertEqual(element.queryTag('{TestNamespace}testD1', ignoreNameSpace=False)[0], "1 2 3")
        self.assertEqual(element.queryTag('testB')[1]['id'], "123")


if __name__ == "__main__":
    unittest.main()
