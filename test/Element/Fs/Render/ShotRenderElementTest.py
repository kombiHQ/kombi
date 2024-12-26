import os
import unittest
from ....BaseTestCase import BaseTestCase
from kombi.Element import Element
from pathlib import Path
from kombi.Element.Fs.Render import ShotRenderElement

class ShotRenderElementTest(BaseTestCase):
    """Test ShotRenderElement element."""

    __exrFile = os.path.join(BaseTestCase.dataTestsDirectory(), "RND-TST-SHT_lighting_beauty_sr.1001.exr")

    def testShotRenderElement(self):
        """
        Test that the ShotRenderElement element test works properly.
        """
        element = Element.create(Path(self.__exrFile))
        self.assertIsInstance(element, ShotRenderElement)

    def testShotRenderElementVariables(self):
        """
        Test that variables are set properly.
        """
        element = Element.create(Path(self.__exrFile))
        self.assertEqual(element.var("type"), "shotRender")
        self.assertEqual(element.var("category"), "render")
        self.assertEqual(element.var("renderType"), "sr")
        self.assertEqual(element.var("seq"), "TST")
        self.assertEqual(element.var("shot"), "RND-TST-SHT")
        self.assertEqual(element.var("step"), "lighting")
        self.assertEqual(element.var("pass"), "beauty")
        self.assertEqual(element.var("renderName"), "lighting-beauty")


if __name__ == "__main__":
    unittest.main()
