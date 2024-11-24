import os
import unittest
from ....BaseTestCase import BaseTestCase
from kombi.InfoCrate import InfoCrate
from kombi.InfoCrate.PathHolder import PathHolder
from kombi.InfoCrate.Fs.Render import TurntableInfoCrate

class TurntableInfoCrateTest(BaseTestCase):
    """Test turntable infoCrate."""

    __exrFile = os.path.join(BaseTestCase.dataTestsDirectory(), "RND_ass_lookdev_default_beauty_tt.1001.exr")

    def testTurntableInfoCrate(self):
        """
        Test that the turntable infoCrate test works properly.
        """
        infoCrate = InfoCrate.create(PathHolder(self.__exrFile))
        self.assertIsInstance(infoCrate, TurntableInfoCrate)

    def testTurntableInfoCrateVariables(self):
        """
        Test that variables are set properly.
        """
        infoCrate = InfoCrate.create(PathHolder(self.__exrFile))
        self.assertEqual(infoCrate.var("type"), "turntable")
        self.assertEqual(infoCrate.var("category"), "render")
        self.assertEqual(infoCrate.var("renderType"), "tt")
        self.assertEqual(infoCrate.var("assetName"), "ass")
        self.assertEqual(infoCrate.var("step"), "lookdev")
        self.assertEqual(infoCrate.var("pass"), "beauty")
        self.assertEqual(infoCrate.var("renderName"), "ass-default-beauty")


if __name__ == "__main__":
    unittest.main()
