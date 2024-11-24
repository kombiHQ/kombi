import os
import unittest
from ....BaseTestCase import BaseTestCase
from kombi.InfoCrate import InfoCrate
from kombi.InfoCrate.Fs.Image import ImageInfoCrate
from kombi.InfoCrate.PathHolder import PathHolder

class ImageInfoCrateTest(BaseTestCase):
    """Test Image infoCrate."""

    __singleFile = os.path.join(BaseTestCase.dataTestsDirectory(), "test.dpx")
    __sequenceFile = os.path.join(BaseTestCase.dataTestsDirectory(), "testSeq.0001.exr")

    def testSingleImage(self):
        """
        Test that the infoCrate created for a single image is based on the image infoCrate.
        """
        infoCrate = InfoCrate.create(PathHolder(self.__singleFile))
        self.assertIsInstance(infoCrate, ImageInfoCrate)

    def testSequenceImage(self):
        """
        Test that the infoCrate created for a sequence image is based on the image infoCrate.
        """
        infoCrate = InfoCrate.create(PathHolder(self.__sequenceFile))
        self.assertIsInstance(infoCrate, ImageInfoCrate)

    def testGroupTagSequence(self):
        """
        Test that the tag group has been assigned to the image sequence infoCrate.
        """
        infoCrate = InfoCrate.create(PathHolder(self.__sequenceFile))

        self.assertIn('group', infoCrate.tagNames())
        self.assertEqual(infoCrate.tag('group'), "testSeq.####.exr")

    def testGroupSprintfTagSequence(self):
        """
        Test that the tag groupSprintf has been assigned to the image sequence infoCrate.
        """
        infoCrate = InfoCrate.create(PathHolder(self.__sequenceFile))
        self.assertIn('groupSprintf', infoCrate.tagNames())
        self.assertEqual(infoCrate.tag('groupSprintf'), "testSeq.%04d.exr")

    def testGroupTagSingle(self):
        """
        Test that the tag group has not been assigned to a single image infoCrate.
        """
        infoCrate = InfoCrate.create(PathHolder(self.__singleFile))
        self.assertNotIn('group', infoCrate.tagNames())

    def testGroupSprintfTagSingle(self):
        """
        Test that the tag groupSprintf has not been assigned to a single image infoCrate.
        """
        infoCrate = InfoCrate.create(PathHolder(self.__singleFile))
        self.assertNotIn('groupSprintf', infoCrate.tagNames())

    def testIsSequence(self):
        """
        Test if a infoCrate is a sequence.
        """
        singleInfoCrate = InfoCrate.create(PathHolder(self.__singleFile))
        sequenceInfoCrate = InfoCrate.create(PathHolder(self.__sequenceFile))

        self.assertEqual(singleInfoCrate.isSequence(), False)
        self.assertEqual(singleInfoCrate.var("imageType"), "single")
        self.assertEqual(sequenceInfoCrate.isSequence(), True)
        self.assertEqual(sequenceInfoCrate.var("imageType"), "sequence")


if __name__ == "__main__":
    unittest.main()
