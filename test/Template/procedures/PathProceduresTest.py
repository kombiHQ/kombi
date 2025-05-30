import unittest
from ...BaseTestCase import BaseTestCase
from kombi.Template import Template
from kombi.Template import TemplateProcedureNotFoundError

class PathProceduresTest(BaseTestCase):
    """Test Path template procedures."""

    __path = "/test/path/example.ext"

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

    def testRegistration(self):
        """
        Test that the procedure registration works properly.
        """
        def myDummyTemplate(a, b):
            return '{}-{}'.format(a, b)

        with self.assertRaises(TemplateProcedureNotFoundError):
            Template.runProcedure("dummyRegistration", 1, 2)

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
