import os
import unittest
from ....BaseTestCase import BaseTestCase
from kombi.InfoCrate.Fs import FsInfoCrate
from kombi.InfoCrate.Fs.Ascii import XmlInfoCrate

class XmlInfoCrateTest(BaseTestCase):
    """Test Xml infoCrate."""

    __xmlFile = os.path.join(BaseTestCase.dataTestsDirectory(), "test.xml")

    def testXmlInfoCrate(self):
        """
        Test that the Xml infoCrate test works properly.
        """
        infoCrate = FsInfoCrate.createFromPath(self.__xmlFile)
        self.assertIsInstance(infoCrate, XmlInfoCrate)

    def testXmlVariables(self):
        """
        Test that variables are set properly.
        """
        infoCrate = FsInfoCrate.createFromPath(self.__xmlFile)
        self.assertEqual(infoCrate.var("type"), "xml")
        self.assertEqual(infoCrate.var("category"), "ascii")

    def testXmlContents(self):
        """
        Test that txt files are parsed properly.
        """
        infoCrate = FsInfoCrate.createFromPath(self.__xmlFile)
        self.assertEqual(infoCrate.queryTag('testC')[0], "testing child C")
        self.assertEqual(infoCrate.queryTag('testD1')[0], "1 2 3")
        self.assertEqual(infoCrate.queryTag('{TestNamespace}testD1', ignoreNameSpace=False)[0], "1 2 3")
        self.assertEqual(infoCrate.queryTag('testB')[1]['id'], "123")


if __name__ == "__main__":
    unittest.main()
