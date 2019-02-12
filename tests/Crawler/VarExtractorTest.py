import unittest
from collections import OrderedDict
from ..BaseTestCase import BaseTestCase
from chilopoda.Crawler.VarExtractor import VarExtractor, VarExtractorNotMatchingCharError, VarExtractorMissingSeparatorError, VarExtractorCannotFindExpectedCharError

class VarExtractorTest(BaseTestCase):
    """Test for var extractor."""

    def testExtractingVars(self):
        """
        Test extracting variables.
        """
        varExtractor = VarExtractor(
            "PRO_ABC_D-E-F_FOO_V0001.0001.png",
            "{job:3}_{seq:3}_*_{plateName}_V{version:4i}.####.{ext}"
        )

        checkData = OrderedDict()
        checkData['job'] = 'PRO'
        checkData['seq'] = 'ABC'
        checkData['plateName'] = 'FOO'
        checkData['version'] = 1
        checkData['ext'] = 'png'

        self.assertTrue(varExtractor.match())
        self.assertListEqual(
            varExtractor.varNames(),
            list(checkData.keys())
        )

        for varName, varValue in checkData.items():
            self.assertEqual(varValue, varExtractor.var(varName))

    def testNotMatchingChar(self):
        """
        Test not matching char error.
        """
        varExtractor = VarExtractor(
            "PRO_ABC_D-E-F_FOO_V0001.0001.png",
            "{job:3}_{seq:3}_*_{plateName}_aV{version:4i}.####.{ext}"
        )

        self.assertFalse(varExtractor.match())

        self.assertIsInstance(
            varExtractor.error(),
            VarExtractorNotMatchingCharError
        )

    def testMissingSeparator(self):
        """
        Test missing separator error.
        """
        varExtractor = VarExtractor(
            "PRO_ABC_D-E-F_FOO_V0001.0001.png",
            "{job:3}_{seq:3}_*{plateName}_V{version:4i}.####.{ext}"
        )

        self.assertFalse(varExtractor.match())

        self.assertIsInstance(
            varExtractor.error(),
            VarExtractorMissingSeparatorError
        )

    def testCannotFindExpectedCharAfterGlob(self):
        """
        Test cannot find expected char after glob.
        """
        self.assertRaises(
            VarExtractorCannotFindExpectedCharError,
            VarExtractor,
            "PRO_ABC_D-E-F_FOO_V0001.0001.png",
            "{job:3}_{seq:3}_*a_{plateName}_V{version:4i}.####.{ext}",
            raiseOnFail=True
        )


if __name__ == "__main__":
    unittest.main()
