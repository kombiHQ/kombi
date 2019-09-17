import unittest
from ...BaseTestCase import BaseTestCase
from kombi.Template import Template

class MathProceduresTest(BaseTestCase):
    """Test Math template procedures."""

    def testSum(self):
        """
        Test that the sum procedure works properly.
        """
        result = Template.runProcedure("sum", 1, 2)
        self.assertEqual(result, "3")

    def testSub(self):
        """
        Test that the sub procedure works properly.
        """
        result = Template.runProcedure("sub", 1, 2)
        self.assertEqual(result, "-1")

    def testMult(self):
        """
        Test that the mult procedure works properly.
        """
        result = Template.runProcedure("mult", 2, 3)
        self.assertEqual(result, "6")

    def testDiv(self):
        """
        Test that the div procedure works properly.
        """
        result = Template.runProcedure("div", 6, 2)
        self.assertEqual(result, "3")

    def testMin(self):
        """
        Test that the min procedure works properly.
        """
        result = Template.runProcedure("min", 6, 2)
        self.assertEqual(result, "2")

    def testMax(self):
        """
        Test that the max procedure works properly.
        """
        result = Template.runProcedure("max", 6, 2)
        self.assertEqual(result, "6")


if __name__ == "__main__":
    unittest.main()
