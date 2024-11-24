import os
import unittest
from ....BaseTestCase import BaseTestCase
from kombi.InfoCrate import InfoCrate
from kombi.InfoCrate.PathHolder import PathHolder
from kombi.InfoCrate.Fs.Ascii import TxtInfoCrate

class TxtInfoCrateTest(BaseTestCase):
    """Test Txt infoCrate."""

    __txtFile = os.path.join(BaseTestCase.dataTestsDirectory(), "test.txt")

    def testTxtInfoCrate(self):
        """
        Test that the Txt infoCrate test works properly.
        """
        infoCrate = InfoCrate.create(PathHolder(self.__txtFile))
        self.assertIsInstance(infoCrate, TxtInfoCrate)

    def testTxtVariables(self):
        """
        Test that variables are set properly.
        """
        infoCrate = InfoCrate.create(PathHolder(self.__txtFile))
        self.assertEqual(infoCrate.var("type"), "txt")
        self.assertEqual(infoCrate.var("category"), "ascii")

    def testTxtContents(self):
        """
        Test that txt files are parsed properly.
        """
        infoCrate = InfoCrate.create(PathHolder(self.__txtFile))
        testData = "testing txt file\nwith random data\n\n1 2 3\n"
        self.assertEqual(infoCrate.contents(), testData)


if __name__ == "__main__":
    unittest.main()
