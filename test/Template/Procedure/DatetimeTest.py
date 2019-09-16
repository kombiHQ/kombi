import unittest
from ...BaseTestCase import BaseTestCase
from kombi.Template import Template

class DatetimeTest(BaseTestCase):
    """Test Datetime template procedures."""

    def testYear(self):
        """
        Test that the year template procedures work properly.
        """
        yyyy = Template.runProcedure("yyyy")
        self.assertGreaterEqual(int(yyyy), 2018)
        yy = Template.runProcedure("yy")
        self.assertEqual(yyyy[-2:], yy)

    def testMonth(self):
        """
        Test that the month procedure works properly.
        """
        mm = Template.runProcedure("mm")
        self.assertGreaterEqual(int(mm), 1)
        self.assertLessEqual(int(mm), 12)

    def testDay(self):
        """
        Test that the day procedure works properly.
        """
        dd = Template.runProcedure("dd")
        self.assertGreaterEqual(int(dd), 1)
        self.assertLessEqual(int(dd), 31)

    def testHour(self):
        """
        Test that the hour procedure works properly.
        """
        hour = Template.runProcedure("hour")
        self.assertGreaterEqual(int(hour), 0)
        self.assertLessEqual(int(hour), 23)

    def testMinute(self):
        """
        Test that the minute procedure works properly.
        """
        minute = Template.runProcedure("minute")
        self.assertGreaterEqual(int(minute), 0)
        self.assertLessEqual(int(minute), 59)

    def testSecond(self):
        """
        Test that the second procedure works properly.
        """
        second = Template.runProcedure("second")
        self.assertGreaterEqual(int(second), 0)
        self.assertLessEqual(int(second), 59)


if __name__ == "__main__":
    unittest.main()
