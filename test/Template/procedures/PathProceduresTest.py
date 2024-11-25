import unittest
import os
from ...BaseTestCase import BaseTestCase
from kombi.Template import Template
from kombi.Template import TemplateProcedureNotFoundError

class PathProceduresTest(BaseTestCase):
    """Test Path template procedures."""

    __path = "/test/path/example.ext"
    __testRFindPath = os.path.join(BaseTestCase.dataTestsDirectory(), 'config', 'test.json')

    def testDirname(self):
        """
        Test that the dirname procedure works properly.
        """
        result = Template.runProcedure("dirname", self.__path)
        self.assertEqual(result, "/test/path")

    def testParentDirname(self):
        """
        Test that the parentdirname procedure works properly.
        """
        result = Template.runProcedure("parentdirname", self.__path)
        self.assertEqual(result, "/test")

    def testBasename(self):
        """
        Test that the basename procedure works properly.
        """
        result = Template.runProcedure("basename", self.__path)
        self.assertEqual(result, "example.ext")

    def testRFindPath(self):
        """
        Test that the rfind procedure works properly.
        """
        result = Template.runProcedure('rfindpath', 'test.txt', self.__testRFindPath)
        testPath = os.path.join(BaseTestCase.dataTestsDirectory(), 'test.txt')
        self.assertEqual(result, testPath)

    def testFindPath(self):
        """
        Test that the find procedure works properly.
        """
        result = Template.runProcedure("findpath", 'TestElement.py', BaseTestCase.dataTestsDirectory())
        testPath = os.path.join(BaseTestCase.dataTestsDirectory(), 'config', 'elements', 'TestElement.py')
        self.assertEqual(result, testPath)

    def testRegistration(self):
        """
        Test that the procedure registration works properly.
        """
        def myDummyTemplate(a, b):
            return '{}-{}'.format(a, b)

        with self.assertRaises(TemplateProcedureNotFoundError):
            Template.runProcedure("dummyRegistration")

        Template.registerProcedure("dummyRegistration", myDummyTemplate)
        self.assertIn("dummyRegistration", Template.registeredProcedureNames())

    def testParseRun(self):
        """
        Test that running a procedure through string parsing works.
        """
        result = Template.evalProcedure("(dirname {})".format(self.__path))
        self.assertEqual(result, "/test/path")
        self.assertRaises(AssertionError, Template.evalProcedure, True)


if __name__ == "__main__":
    unittest.main()
