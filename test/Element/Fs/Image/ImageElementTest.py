import os
import unittest
from ....BaseTestCase import BaseTestCase
from kombi.Element import Element
from kombi.Element.Fs.Image import ImageElement
from pathlib import Path

class ImageElementTest(BaseTestCase):
    """Test Image element."""

    __singleFile = os.path.join(BaseTestCase.dataTestsDirectory(), "test.dpx")
    __sequenceFile = os.path.join(BaseTestCase.dataTestsDirectory(), "testSeq.0001.exr")

    def testSingleImage(self):
        """
        Test that the element created for a single image is based on the image element.
        """
        element = Element.create(Path(self.__singleFile))
        self.assertIsInstance(element, ImageElement)

    def testSequenceImage(self):
        """
        Test that the element created for a sequence image is based on the image element.
        """
        element = Element.create(Path(self.__sequenceFile))
        self.assertIsInstance(element, ImageElement)

    def testGroupTagSequence(self):
        """
        Test that the tag group has been assigned to the image sequence element.
        """
        element = Element.create(Path(self.__sequenceFile))

        self.assertIn('group', element.tagNames())
        self.assertEqual(element.tag('group'), "testSeq.####.exr")

    def testGroupSprintfTagSequence(self):
        """
        Test that the tag groupSprintf has been assigned to the image sequence element.
        """
        element = Element.create(Path(self.__sequenceFile))
        self.assertIn('groupSprintf', element.tagNames())
        self.assertEqual(element.tag('groupSprintf'), "testSeq.%04d.exr")

    def testGroupTagSingle(self):
        """
        Test that the tag group has not been assigned to a single image element.
        """
        element = Element.create(Path(self.__singleFile))
        self.assertNotIn('group', element.tagNames())

    def testGroupSprintfTagSingle(self):
        """
        Test that the tag groupSprintf has not been assigned to a single image element.
        """
        element = Element.create(Path(self.__singleFile))
        self.assertNotIn('groupSprintf', element.tagNames())

    def testIsSequence(self):
        """
        Test if a element is a sequence.
        """
        singleElement = Element.create(Path(self.__singleFile))
        sequenceElement = Element.create(Path(self.__sequenceFile))

        self.assertEqual(singleElement.isSequence(), False)
        self.assertEqual(singleElement.var("imageType"), "single")
        self.assertEqual(sequenceElement.isSequence(), True)
        self.assertEqual(sequenceElement.var("imageType"), "sequence")


if __name__ == "__main__":
    unittest.main()
