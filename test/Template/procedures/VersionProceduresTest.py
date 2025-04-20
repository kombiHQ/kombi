import unittest
import os
from ...BaseTestCase import BaseTestCase
from kombi.Template import Template

class VersionProceduresTest(BaseTestCase):
    """Test Version template procedures."""

    def testVersionEmptyPrefixCustomPattern(self):
        """
        Test that the version prefix procedure works with a custom version without prefix.
        """
        customPattern = '#####d'
        result = Template.runProcedure('verprefix', '00005d', customPattern)
        self.assertEqual(result, '')

    def testVersionPrefixCustomPattern(self):
        """
        Test that the version prefix procedure works with a custom version.
        """
        customPattern = 'abc#####d'
        result = Template.runProcedure('verprefix', 'abc00005d', customPattern)
        self.assertEqual(result, 'abc')

    def testVersionNumberCustomPattern(self):
        """
        Test that the version number procedure works with a custom version.
        """
        customPattern = 'abc#####d'
        result = Template.runProcedure('vernumber', 'abc00005d', customPattern)
        self.assertEqual(result, '00005')

    def testVersionNumberOnlyDigitsCustomPattern(self):
        """
        Test that the version number procedure works with a custom version that contains only the digits.
        """
        customPattern = '#####'
        result = Template.runProcedure('vernumber', '00005', customPattern)
        self.assertEqual(result, '00005')

    def testVersionEmptySuffixCustomPattern(self):
        """
        Test that the version suffix procedure works with a custom version without suffix.
        """
        customPattern = 'abc#####'
        result = Template.runProcedure('versuffix', 'abc00005', customPattern)
        self.assertEqual(result, '')

    def testVersionSuffixCustomPattern(self):
        """
        Test that the version suffix procedure works with a custom version.
        """
        customPattern = 'd#####abc'
        result = Template.runProcedure('versuffix', 'd00005abc', customPattern)
        self.assertEqual(result, 'abc')

    def testLabelVersion(self):
        """
        Test that label procedure works properly.
        """
        result = Template.runProcedure('labelver', 3)
        self.assertEqual(result, 'v0003')

    def testLabelVersionCustomPattern(self):
        """
        Test that the label procedure works with a custom version pattern using only digits.
        """
        customPattern = '#####'
        result = Template.runProcedure('labelver', 5, customPattern)
        self.assertEqual(result, '00005')

    def testLabelVersionCustomPrefixPattern(self):
        """
        Test that the label procedure works with a custom version pattern with prefix.
        """
        customPattern = 'a#####'
        result = Template.runProcedure('labelver', 5, customPattern)
        self.assertEqual(result, 'a00005')

    def testLabelVersionCustomSuffixPattern(self):
        """
        Test that the label procedure works with a custom version pattern with suffix.
        """
        customPattern = '#####b'
        result = Template.runProcedure('labelver', 5, customPattern)
        self.assertEqual(result, '00005b')

    def testLabelVersionCustomFullPattern(self):
        """
        Test that the label procedure works with a custom version using full pattern.
        """
        customPattern = 'ab#####_cd'
        result = Template.runProcedure('labelver', 5, customPattern)
        self.assertEqual(result, 'ab00005_cd')

    def testNewVersion(self):
        """
        Test that the new procedure works properly.
        """
        result = Template.runProcedure('newver', BaseTestCase.dataTestsDirectory())
        self.assertEqual(result, 'v0003')

    def testNewVersionCustomPattern(self):
        """
        Test that the new procedure works with a custom version pattern.
        """
        customPattern = 'v#####b'
        result = Template.runProcedure('newver', BaseTestCase.dataTestsDirectory(), customPattern)
        self.assertEqual(result, 'v00005b')

    def testLatestVersion(self):
        """
        Test that the latest version is found properly.
        """
        result = Template.runProcedure('latestver', BaseTestCase.dataTestsDirectory())
        self.assertEqual(result, 'v0002')
        result = Template.runProcedure('latestver', os.path.join(BaseTestCase.dataTestsDirectory(), 'glob'))
        self.assertEqual(result, 'v0000')

    def testLatestVersionCustomPattern(self):
        """
        Test that the new procedure works with a custom version pattern.
        """
        customPattern = 'v#####b'
        result = Template.runProcedure('latestver', BaseTestCase.dataTestsDirectory(), customPattern)
        self.assertEqual(result, 'v00004b')


if __name__ == "__main__":
    unittest.main()
