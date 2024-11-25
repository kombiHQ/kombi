import os
import unittest
from ....BaseTestCase import BaseTestCase
from kombi.Element import Element
from kombi.Element.PathHolder import PathHolder
from kombi.Element.Fs.Scene import MayaSceneElement
from kombi.Element.Fs.Scene import SceneElement


class MayaSceneElementTest(BaseTestCase):
    """Test Maya Scene element."""

    __maFile = os.path.join(BaseTestCase.dataTestsDirectory(), "test.ma")
    __mbFile = os.path.join(BaseTestCase.dataTestsDirectory(), "test.mb")

    def testMayaSceneElement(self):
        """
        Test that the Maya Scene element test works properly.
        """
        element = Element.create(PathHolder(self.__maFile))
        self.assertIsInstance(element, MayaSceneElement)
        element = Element.create(PathHolder(self.__mbFile))
        self.assertIsInstance(element, MayaSceneElement)

    def testMayaSceneVariables(self):
        """
        Test that variables are set properly.
        """
        element = Element.create(PathHolder(self.__maFile))
        self.assertEqual(element.var("type"), "mayaScene")
        self.assertEqual(element.var("category"), "scene")

    def testMayaSceneExtensions(self):
        """
        Test that the list of extensions matching maya scenes is correct.
        """
        self.assertCountEqual(MayaSceneElement.extensions(), ["ma", "mb"])
        self.assertRaises(NotImplementedError, SceneElement.extensions)


if __name__ == "__main__":
    unittest.main()
