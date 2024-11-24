import os
import unittest
from ....BaseTestCase import BaseTestCase
from kombi.InfoCrate import InfoCrate
from kombi.InfoCrate.PathHolder import PathHolder
from kombi.InfoCrate.Fs.Render import NukeRenderInfoCrate

class NukeRenderInfoCrateTest(BaseTestCase):
    """Test NukeRenderInfoCrate infoCrate."""

    __exrFile = os.path.join(BaseTestCase.dataTestsDirectory(), "RND-TST-SHT_comp_compName_output_v010_tk.1001.exr")

    def testNukeRenderInfoCrate(self):
        """
        Test that the NukeRenderInfoCrate infoCrate test works properly.
        """
        infoCrate = InfoCrate.create(PathHolder(self.__exrFile))
        self.assertIsInstance(infoCrate, NukeRenderInfoCrate)

    def testNukeRenderInfoCrateVariables(self):
        """
        Test that variables are set properly.
        """
        infoCrate = InfoCrate.create(PathHolder(self.__exrFile))
        self.assertEqual(infoCrate.var("type"), "nukeRender")
        self.assertEqual(infoCrate.var("category"), "render")
        self.assertEqual(infoCrate.var("renderType"), "tk")
        self.assertEqual(infoCrate.var("seq"), "TST")
        self.assertEqual(infoCrate.var("shot"), "RND-TST-SHT")
        self.assertEqual(infoCrate.var("step"), "comp")
        self.assertEqual(infoCrate.var("renderName"), "compName")
        self.assertEqual(infoCrate.var("output"), "output")
        self.assertEqual(infoCrate.var("versionName"), "v010")
        self.assertEqual(infoCrate.var("version"), 10)


if __name__ == "__main__":
    unittest.main()
