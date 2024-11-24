import unittest
from collections import OrderedDict
from ..BaseTestCase import BaseTestCase
from kombi.InfoCrate.VarExtractor import VarExtractor, VarExtractorNotMatchingCharError, VarExtractorMissingSeparatorError, VarExtractorCannotFindExpectedCharError

class VarExtractorTest(BaseTestCase):
    """Test for var extractor."""

    def testExtractingVarsFromPro(self):
        """
        Test extracting variables from project pro.
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

    def testExtractingVarsFromFoo(self):
        """
        Test extracting variables from project foo.
        """
        varExtractor = VarExtractor(
            "foo_abc_def_v002.000001.exr",
            "{job:3}_{seq:3}_{shot:3}_v{version:3i}.######.{ext}"
        )

        checkData = OrderedDict()
        checkData['job'] = 'foo'
        checkData['seq'] = 'abc'
        checkData['shot'] = 'def'
        checkData['version'] = 2
        checkData['ext'] = 'exr'

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

    def testNotMatchingCharNumericCastError(self):
        """
        Test not matching char error by failing to cast to a numeric value.
        """
        varExtractor = VarExtractor(
            "foo_abc_def_v001.000001.exr",
            "{job:3}_{seq:3}_{shot:3}_v{version:4i}.######.exr"
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
