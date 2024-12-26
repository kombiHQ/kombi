import os
import unittest
from ....BaseTestCase import BaseTestCase
from kombi.Element import Element
from pathlib import Path
from kombi.Element.Fs.Render import NukeRenderElement

class NukeRenderElementTest(BaseTestCase):
    """Test NukeRenderElement element."""

    __exrFile = os.path.join(BaseTestCase.dataTestsDirectory(), "RND-TST-SHT_comp_compName_output_v010_tk.1001.exr")

    def testNukeRenderElement(self):
        """
        Test that the NukeRenderElement element test works properly.
        """
        element = Element.create(Path(self.__exrFile))
        self.assertIsInstance(element, NukeRenderElement)

    def testNukeRenderElementVariables(self):
        """
        Test that variables are set properly.
        """
        element = Element.create(Path(self.__exrFile))
        self.assertEqual(element.var("type"), "nukeRender")
        self.assertEqual(element.var("category"), "render")
        self.assertEqual(element.var("renderType"), "tk")
        self.assertEqual(element.var("seq"), "TST")
        self.assertEqual(element.var("shot"), "RND-TST-SHT")
        self.assertEqual(element.var("step"), "comp")
        self.assertEqual(element.var("renderName"), "compName")
        self.assertEqual(element.var("output"), "output")
        self.assertEqual(element.var("versionName"), "v010")
        self.assertEqual(element.var("version"), 10)


if __name__ == "__main__":
    unittest.main()
