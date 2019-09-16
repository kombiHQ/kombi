import unittest
import getpass
import os
import tempfile
from ...BaseTestCase import BaseTestCase
from kombi.Template import Template

class SystemTest(BaseTestCase):
    """Test System template procedures."""

    def testTmp(self):
        """
        Test that the tmp procedure works properly.
        """
        result = Template.runProcedure("tmp")
        self.assertEqual(result, tempfile.gettempdir())

    def testTmpdir(self):
        """
        Test that the tmpdir procedure works properly.
        """
        result = Template.runProcedure("tmpdir")
        self.assertFalse(os.path.exists(result))

    def testEnv(self):
        """
        Test that the env procedure works properly.
        """
        userEnvironment = 'USER' if 'USER' in os.environ else 'USERNAME'

        result = Template.runProcedure("env", userEnvironment)
        self.assertEqual(result, getpass.getuser())


if __name__ == "__main__":
    unittest.main()
