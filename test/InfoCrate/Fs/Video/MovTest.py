import os
import unittest
from ....BaseTestCase import BaseTestCase
from kombi.InfoCrate import InfoCrate
from kombi.InfoCrate.PathHolder import PathHolder
from kombi.InfoCrate.Fs.Video import MovInfoCrate

class MovTest(BaseTestCase):
    """Test Texture infoCrate."""

    __movFile = os.path.join(BaseTestCase.dataTestsDirectory(), "video.mov")
    __movNoTimecodeFile = os.path.join(BaseTestCase.dataTestsDirectory(), "videoNoTimeCode.mov")

    def testMovInfoCrate(self):
        """
        Test that the Mov infoCrate test works properly.
        """
        infoCrate = InfoCrate.create(PathHolder(self.__movFile))
        self.assertIsInstance(infoCrate, MovInfoCrate)

    def testMovVariables(self):
        """
        Test that variables are set properly.
        """
        infoCrate = InfoCrate.create(PathHolder(self.__movFile))
        self.assertEqual(infoCrate.var("type"), "mov")
        self.assertEqual(infoCrate.var("category"), "video")
        self.assertEqual(infoCrate.var("width"), 1920)
        self.assertEqual(infoCrate.var("height"), 1080)
        self.assertEqual(infoCrate.var("firstFrame"), 1)
        self.assertEqual(infoCrate.var("lastFrame"), 12)

        infoCrate = InfoCrate.create(PathHolder(self.__movNoTimecodeFile))
        self.assertEqual(infoCrate.var("firstFrame"), 0)
        self.assertEqual(infoCrate.var("lastFrame"), 23)

    def testMovTags(self):
        """
        Test that the tags are set properly.
        """
        infoCrate = InfoCrate.create(PathHolder(self.__movFile))
        self.assertEqual(infoCrate.tag("video"), "video.mov")


if __name__ == "__main__":
    unittest.main()
