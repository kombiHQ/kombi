import os
import unittest
from ....BaseTestCase import BaseTestCase
from kombi.Element import Element
from kombi.Element.PathHolder import PathHolder
from kombi.Element.Fs.Video import MovElement

class MovTest(BaseTestCase):
    """Test Texture element."""

    __movFile = os.path.join(BaseTestCase.dataTestsDirectory(), "video.mov")
    __movNoTimecodeFile = os.path.join(BaseTestCase.dataTestsDirectory(), "videoNoTimeCode.mov")

    def testMovElement(self):
        """
        Test that the Mov element test works properly.
        """
        element = Element.create(PathHolder(self.__movFile))
        self.assertIsInstance(element, MovElement)

    def testMovVariables(self):
        """
        Test that variables are set properly.
        """
        element = Element.create(PathHolder(self.__movFile))
        self.assertEqual(element.var("type"), "mov")
        self.assertEqual(element.var("category"), "video")
        self.assertEqual(element.var("width"), 1920)
        self.assertEqual(element.var("height"), 1080)
        self.assertEqual(element.var("firstFrame"), 1)
        self.assertEqual(element.var("lastFrame"), 12)

        element = Element.create(PathHolder(self.__movNoTimecodeFile))
        self.assertEqual(element.var("firstFrame"), 0)
        self.assertEqual(element.var("lastFrame"), 23)

    def testMovTags(self):
        """
        Test that the tags are set properly.
        """
        element = Element.create(PathHolder(self.__movFile))
        self.assertEqual(element.tag("video"), "video.mov")


if __name__ == "__main__":
    unittest.main()
