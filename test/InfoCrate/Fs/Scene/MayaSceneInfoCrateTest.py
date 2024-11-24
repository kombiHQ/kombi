import os
import unittest
from ....BaseTestCase import BaseTestCase
from kombi.InfoCrate import InfoCrate
from kombi.InfoCrate.PathHolder import PathHolder
from kombi.InfoCrate.Fs.Scene import MayaSceneInfoCrate
from kombi.InfoCrate.Fs.Scene import SceneInfoCrate


class MayaSceneInfoCrateTest(BaseTestCase):
    """Test Maya Scene infoCrate."""

    __maFile = os.path.join(BaseTestCase.dataTestsDirectory(), "test.ma")
    __mbFile = os.path.join(BaseTestCase.dataTestsDirectory(), "test.mb")

    def testMayaSceneInfoCrate(self):
        """
        Test that the Maya Scene infoCrate test works properly.
        """
        infoCrate = InfoCrate.create(PathHolder(self.__maFile))
        self.assertIsInstance(infoCrate, MayaSceneInfoCrate)
        infoCrate = InfoCrate.create(PathHolder(self.__mbFile))
        self.assertIsInstance(infoCrate, MayaSceneInfoCrate)

    def testMayaSceneVariables(self):
        """
        Test that variables are set properly.
        """
        infoCrate = InfoCrate.create(PathHolder(self.__maFile))
        self.assertEqual(infoCrate.var("type"), "mayaScene")
        self.assertEqual(infoCrate.var("category"), "scene")

    def testMayaSceneExtensions(self):
        """
        Test that the list of extensions matching maya scenes is correct.
        """
        self.assertCountEqual(MayaSceneInfoCrate.extensions(), ["ma", "mb"])
        self.assertRaises(NotImplementedError, SceneInfoCrate.extensions)


if __name__ == "__main__":
    unittest.main()
