import unittest
import getpass
import os
import tempfile
from ...BaseTestCase import BaseTestCase
from kombi.Template import Template

class SystemProceduresTest(BaseTestCase):
    """Test System template procedures."""

    def testTmp(self):
        """
        Test that the tmp procedure works properly.
        """
        currentValue = os.environ.get('KOMBI_TEMP_REMOTE_DIR', None)
        os.environ.pop('KOMBI_TEMP_REMOTE_DIR')

        try:
            result = Template.runProcedure("tmp")
            self.assertEqual(result, tempfile.gettempdir())
        finally:
            if currentValue:
                os.environ['KOMBI_TEMP_REMOTE_DIR'] = currentValue

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
