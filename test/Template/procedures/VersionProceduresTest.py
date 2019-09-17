import unittest
import os
from ...BaseTestCase import BaseTestCase
from kombi.Template import Template

class VersionProceduresTest(BaseTestCase):
    """Test Version template procedures."""

    def testNewVersion(self):
        """
        Test that the new procedure works properly.
        """
        result = Template.runProcedure("newver", BaseTestCase.dataTestsDirectory())
        self.assertEqual(result, "v003")

    def testLatestVersion(self):
        """
        Test that the latest version is found properly.
        """
        result = Template.runProcedure("latestver", BaseTestCase.dataTestsDirectory())
        self.assertEqual(result, "v002")
        result = Template.runProcedure("latestver", os.path.join(BaseTestCase.dataTestsDirectory(), "glob"))
        self.assertEqual(result, "v000")


if __name__ == "__main__":
    unittest.main()
