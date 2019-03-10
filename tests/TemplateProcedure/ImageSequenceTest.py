import unittest
from ..BaseTestCase import BaseTestCase
from kombi.Template import Template

class ImageSequenceTest(BaseTestCase):
    """Test ImageSequence template procedures."""

    def testPadding(self):
        """
        Test that the padding procedure works properly.
        """
        padding = Template.runProcedure("pad", 1, 4)
        self.assertEqual(padding, "0001")
        padding = Template.runProcedure("pad", 100, 6)
        self.assertEqual(padding, "000100")

    def testRetimePadding(self):
        """
        Test that the retime padding procedure works properly.
        """
        padding = Template.runProcedure("retimepad", 1, 5, 4)
        self.assertEqual(padding, "0006")
        padding = Template.runProcedure("retimepad", 100, -99, 6)
        self.assertEqual(padding, "000001")


if __name__ == "__main__":
    unittest.main()
