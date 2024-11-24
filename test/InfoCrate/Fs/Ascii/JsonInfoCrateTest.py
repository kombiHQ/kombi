import os
import unittest
from ....BaseTestCase import BaseTestCase
from kombi.InfoCrate import InfoCrate
from kombi.InfoCrate.PathHolder import PathHolder
from kombi.InfoCrate.Fs.Ascii import JsonInfoCrate

class JsonInfoCrateTest(BaseTestCase):
    """Test Json infoCrate."""

    __jsonFile = os.path.join(BaseTestCase.dataTestsDirectory(), "test.json")

    def testJsonInfoCrate(self):
        """
        Test that the Json infoCrate test works properly.
        """
        infoCrate = InfoCrate.create(PathHolder(self.__jsonFile))
        self.assertIsInstance(infoCrate, JsonInfoCrate)

    def testJsonVariables(self):
        """
        Test that variables are set properly.
        """
        infoCrate = InfoCrate.create(PathHolder(self.__jsonFile))
        self.assertEqual(infoCrate.var("type"), "json")
        self.assertEqual(infoCrate.var("category"), "ascii")

    def testJsonContents(self):
        """
        Test that json files are parsed properly.
        """
        infoCrate = InfoCrate.create(PathHolder(self.__jsonFile))
        testData = {
            "testList": [1, 1.2, "value"],
            "testDict": {"key": "value", "number": 1},
            "testString": "blah"
        }
        self.assertEqual(infoCrate.contents(), testData)


if __name__ == "__main__":
    unittest.main()
