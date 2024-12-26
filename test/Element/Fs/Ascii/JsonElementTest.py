import os
import unittest
from ....BaseTestCase import BaseTestCase
from kombi.Element import Element
from pathlib import Path
from kombi.Element.Fs.Ascii import JsonElement

class JsonElementTest(BaseTestCase):
    """Test Json element."""

    __jsonFile = os.path.join(BaseTestCase.dataTestsDirectory(), "test.json")

    def testJsonElement(self):
        """
        Test that the Json element test works properly.
        """
        element = Element.create(Path(self.__jsonFile))
        self.assertIsInstance(element, JsonElement)

    def testJsonVariables(self):
        """
        Test that variables are set properly.
        """
        element = Element.create(Path(self.__jsonFile))
        self.assertEqual(element.var("type"), "json")
        self.assertEqual(element.var("category"), "ascii")

    def testJsonContents(self):
        """
        Test that json files are parsed properly.
        """
        element = Element.create(Path(self.__jsonFile))
        testData = {
            "testList": [1, 1.2, "value"],
            "testDict": {"key": "value", "number": 1},
            "testString": "blah"
        }
        self.assertEqual(element.contents(), testData)


if __name__ == "__main__":
    unittest.main()
