import os
import unittest
from ....BaseTestCase import BaseTestCase
from kombi.InfoCrate import InfoCrate
from kombi.InfoCrate.PathHolder import PathHolder
from kombi.InfoCrate.Fs.Render import ShotRenderInfoCrate

class ShotRenderInfoCrateTest(BaseTestCase):
    """Test ShotRenderInfoCrate infoCrate."""

    __exrFile = os.path.join(BaseTestCase.dataTestsDirectory(), "RND-TST-SHT_lighting_beauty_sr.1001.exr")

    def testShotRenderInfoCrate(self):
        """
        Test that the ShotRenderInfoCrate infoCrate test works properly.
        """
        infoCrate = InfoCrate.create(PathHolder(self.__exrFile))
        self.assertIsInstance(infoCrate, ShotRenderInfoCrate)

    def testShotRenderInfoCrateVariables(self):
        """
        Test that variables are set properly.
        """
        infoCrate = InfoCrate.create(PathHolder(self.__exrFile))
        self.assertEqual(infoCrate.var("type"), "shotRender")
        self.assertEqual(infoCrate.var("category"), "render")
        self.assertEqual(infoCrate.var("renderType"), "sr")
        self.assertEqual(infoCrate.var("seq"), "TST")
        self.assertEqual(infoCrate.var("shot"), "RND-TST-SHT")
        self.assertEqual(infoCrate.var("step"), "lighting")
        self.assertEqual(infoCrate.var("pass"), "beauty")
        self.assertEqual(infoCrate.var("renderName"), "lighting-beauty")


if __name__ == "__main__":
    unittest.main()
