import os
import unittest
import glob
from ....BaseTestCase import BaseTestCase
from kombi.InfoCrate import InfoCrate
from kombi.InfoCrate.PathHolder import PathHolder
from kombi.InfoCrate.Fs.Image import ExrInfoCrate

class ExrInfoCrateTest(BaseTestCase):
    """Test Exr infoCrate."""

    __exrFile = os.path.join(BaseTestCase.dataTestsDirectory(), "test.exr")
    __exrSeq = os.path.join(BaseTestCase.dataTestsDirectory(), "testSeq.0001.exr")
    __exrAmbiguousSeq = os.path.join(BaseTestCase.dataTestsDirectory(), "test_0001.exr")

    def testExrInfoCrate(self):
        """
        Test that the Exr infoCrate test works properly.
        """
        infoCrate = InfoCrate.create(PathHolder(self.__exrFile))
        self.assertIsInstance(infoCrate, ExrInfoCrate)
        infoCrate = InfoCrate.create(PathHolder(BaseTestCase.dataTestsDirectory()))
        self.assertNotIsInstance(infoCrate, ExrInfoCrate)

    def testExrVariables(self):
        """
        Test that variables are set properly.
        """
        infoCrate = InfoCrate.create(PathHolder(self.__exrFile))
        self.assertEqual(infoCrate.var("type"), "exr")
        self.assertEqual(infoCrate.var("category"), "image")
        self.assertEqual(infoCrate.var("imageType"), "single")

    def testExrWidthHeight(self):
        """
        Test that width and height variables are processed properly.
        """
        infoCrate = InfoCrate.create(PathHolder(self.__exrFile))
        self.assertNotIn("width", infoCrate.varNames())
        self.assertNotIn("height", infoCrate.varNames())
        self.assertEqual(infoCrate.var("width"), 1920)
        self.assertEqual(infoCrate.var("height"), 1080)

    def testImageSequence(self):
        """
        Test that detection of an image sequence works properly.
        """
        infoCrate = InfoCrate.create(PathHolder(self.__exrFile))
        self.assertFalse(infoCrate.isSequence())
        infoCrate = InfoCrate.create(PathHolder(self.__exrSeq))
        self.assertTrue(infoCrate.isSequence())
        infoCrate = InfoCrate.create(PathHolder(self.__exrAmbiguousSeq))
        self.assertTrue(infoCrate.isSequence())

    def testImageSequenceVariables(self):
        """
        Test that the image sequence related variables are set properly.
        """
        infoCrate = InfoCrate.create(PathHolder(self.__exrSeq))
        self.assertEqual(infoCrate.var("imageType"), "sequence")
        self.assertEqual(infoCrate.var("name"), "testSeq")
        self.assertEqual(infoCrate.var("frame"), 1)
        self.assertEqual(infoCrate.var("padding"), 4)
        infoCrate = InfoCrate.create(PathHolder(self.__exrAmbiguousSeq))
        self.assertEqual(infoCrate.var("imageType"), "sequence")
        self.assertEqual(infoCrate.var("name"), "test")
        self.assertEqual(infoCrate.var("frame"), 1)
        self.assertEqual(infoCrate.var("padding"), 4)

    def testImageSequenceGroup(self):
        """
        Test that an image sequence is grouped properly.
        """
        paths = glob.glob("{}/testSeq.*.exr".format(self.dataTestsDirectory()))
        infoCrates = list(map(lambda x: InfoCrate.create(PathHolder(x)), paths))
        infoCrates.append(InfoCrate.create(PathHolder(self.__exrFile)))
        grouped = ExrInfoCrate.group(infoCrates)
        self.assertEqual(len(grouped), 2)
        self.assertEqual(len(grouped[0]), len(paths))
        self.assertEqual(len(grouped[1]), 1)
        groupedPaths = list(map(lambda x: x.var("filePath"), grouped[0]))
        self.assertEqual(groupedPaths, sorted(paths))
        self.assertEqual(grouped[1][0].var("filePath"), self.__exrFile)
        reversedGrouped = ExrInfoCrate.sortGroup(grouped, lambda x: x.var('filePath'), True)
        reversedPaths = list(map(lambda x: x.var("filePath"), reversedGrouped[0]))
        self.assertEqual(reversedPaths, sorted(paths, reverse=True))


if __name__ == "__main__":
    unittest.main()
