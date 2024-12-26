import os
import unittest
import glob
from ....BaseTestCase import BaseTestCase
from kombi.Element import Element
from pathlib import Path
from kombi.Element.Fs.Image import ExrElement

class ExrElementTest(BaseTestCase):
    """Test Exr element."""

    __exrFile = os.path.join(BaseTestCase.dataTestsDirectory(), "test.exr")
    __exrSeq = os.path.join(BaseTestCase.dataTestsDirectory(), "testSeq.0001.exr")
    __exrAmbiguousSeq = os.path.join(BaseTestCase.dataTestsDirectory(), "test_0001.exr")

    def testExrElement(self):
        """
        Test that the Exr element test works properly.
        """
        element = Element.create(Path(self.__exrFile))
        self.assertIsInstance(element, ExrElement)
        element = Element.create(Path(BaseTestCase.dataTestsDirectory()))
        self.assertNotIsInstance(element, ExrElement)

    def testExrVariables(self):
        """
        Test that variables are set properly.
        """
        element = Element.create(Path(self.__exrFile))
        self.assertEqual(element.var("type"), "exr")
        self.assertEqual(element.var("category"), "image")
        self.assertEqual(element.var("imageType"), "single")

    def testExrWidthHeight(self):
        """
        Test that width and height variables are processed properly.
        """
        element = Element.create(Path(self.__exrFile))
        self.assertNotIn("width", element.varNames())
        self.assertNotIn("height", element.varNames())
        self.assertEqual(element.var("width"), 1920)
        self.assertEqual(element.var("height"), 1080)

    def testImageSequence(self):
        """
        Test that detection of an image sequence works properly.
        """
        element = Element.create(Path(self.__exrFile))
        self.assertFalse(element.isSequence())
        element = Element.create(Path(self.__exrSeq))
        self.assertTrue(element.isSequence())
        element = Element.create(Path(self.__exrAmbiguousSeq))
        self.assertTrue(element.isSequence())

    def testImageSequenceVariables(self):
        """
        Test that the image sequence related variables are set properly.
        """
        element = Element.create(Path(self.__exrSeq))
        self.assertEqual(element.var("imageType"), "sequence")
        self.assertEqual(element.var("name"), "testSeq")
        self.assertEqual(element.var("frame"), 1)
        self.assertEqual(element.var("padding"), 4)
        element = Element.create(Path(self.__exrAmbiguousSeq))
        self.assertEqual(element.var("imageType"), "sequence")
        self.assertEqual(element.var("name"), "test")
        self.assertEqual(element.var("frame"), 1)
        self.assertEqual(element.var("padding"), 4)

    def testImageSequenceGroup(self):
        """
        Test that an image sequence is grouped properly.
        """
        paths = glob.glob("{}/testSeq.*.exr".format(self.dataTestsDirectory()))
        elements = list(map(lambda x: Element.create(Path(x)), paths))
        elements.append(Element.create(Path(self.__exrFile)))
        grouped = ExrElement.group(elements)
        self.assertEqual(len(grouped), 2)
        self.assertEqual(len(grouped[0]), len(paths))
        self.assertEqual(len(grouped[1]), 1)
        groupedPaths = list(map(lambda x: x.var("filePath"), grouped[0]))
        self.assertEqual(groupedPaths, sorted(paths))
        self.assertEqual(grouped[1][0].var("filePath"), self.__exrFile)
        reversedGrouped = ExrElement.sortGroup(grouped, lambda x: x.var('filePath'), True)
        reversedPaths = list(map(lambda x: x.var("filePath"), reversedGrouped[0]))
        self.assertEqual(reversedPaths, sorted(paths, reverse=True))


if __name__ == "__main__":
    unittest.main()
