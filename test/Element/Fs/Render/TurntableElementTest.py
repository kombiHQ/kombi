import os
import unittest
from ....BaseTestCase import BaseTestCase
from kombi.Element import Element
from kombi.Element.PathHolder import PathHolder
from kombi.Element.Fs.Render import TurntableElement

class TurntableElementTest(BaseTestCase):
    """Test turntable element."""

    __exrFile = os.path.join(BaseTestCase.dataTestsDirectory(), "RND_ass_lookdev_default_beauty_tt.1001.exr")

    def testTurntableElement(self):
        """
        Test that the turntable element test works properly.
        """
        element = Element.create(PathHolder(self.__exrFile))
        self.assertIsInstance(element, TurntableElement)

    def testTurntableElementVariables(self):
        """
        Test that variables are set properly.
        """
        element = Element.create(PathHolder(self.__exrFile))
        self.assertEqual(element.var("type"), "turntable")
        self.assertEqual(element.var("category"), "render")
        self.assertEqual(element.var("renderType"), "tt")
        self.assertEqual(element.var("assetName"), "ass")
        self.assertEqual(element.var("step"), "lookdev")
        self.assertEqual(element.var("pass"), "beauty")
        self.assertEqual(element.var("renderName"), "ass-default-beauty")


if __name__ == "__main__":
    unittest.main()
