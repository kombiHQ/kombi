import os
import unittest
from ...BaseTestCase import BaseTestCase
from kombi.Element import Element
from pathlib import Path
from kombi.Element.Fs import DirectoryElement

class DirectoryElementTest(BaseTestCase):
    """Test Directory element."""

    __dir = os.path.join(BaseTestCase.dataTestsDirectory(), "640x480")

    def testDirectoryElement(self):
        """
        Test that the Directory element test works properly.
        """
        element = Element.create(Path(self.__dir))
        self.assertIsInstance(element, DirectoryElement)

    def testDirectoryVariables(self):
        """
        Test that the variables are set properly.
        """
        element = Element.create(Path(self.__dir))
        self.assertEqual(element.var("width"), 640)
        self.assertEqual(element.var("height"), 480)

    def testIsLeaf(self):
        """
        Test to show directory element is not a leaf.
        """
        element = Element.create(Path(self.__dir))
        self.assertFalse(element.isLeaf())

    def testBadFile(self):
        """
        Test to show that file names with illegal characters are skipped.
        """
        element = Element.create(Path(self.dataTestsDirectory()))
        elementPaths = map(lambda x: x.var("filePath"), element.children())
        self.assertNotIn(os.path.join(self.__dir, "bad file.txt"), elementPaths)


if __name__ == "__main__":
    unittest.main()
