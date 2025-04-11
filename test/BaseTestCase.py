import os
import sys
import shutil
import fnmatch
import tempfile
import unittest

# querying root directory
root = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))

# Add kombi source code to python path for tests
sourceFolder = os.path.join(root, "src", "lib")
if not os.path.exists(sourceFolder):  # pragma: no cover
    raise Exception("Can't resolve lib location!")

sys.path.insert(1, sourceFolder)

class BaseTestCase(unittest.TestCase):
    """Base class for kombi unit tests."""

    __rootPath = root
    __tempDirectory = None

    @classmethod
    def collectFiles(cls, rootDirectory, filterMask='*'):
        """
        Return a list of files located inside of the root directory (recursively).
        """
        result = []

        for root, dirnames, filenames in os.walk(rootDirectory):
            for filename in fnmatch.filter(filenames + dirnames, filterMask):
                result.append(os.path.join(root, filename))
        return result

    @classmethod
    def rootPath(cls):
        """
        Return kombi code root path.
        """
        return cls.__rootPath

    @classmethod
    def tempDirectory(cls):
        """
        Return a temporary directory used to write the test data.
        """
        if cls.__tempDirectory is None:
            cls.__tempDirectory = tempfile.mkdtemp()

        os.makedirs(cls.__tempDirectory, exist_ok=True)
        return cls.__tempDirectory

    @classmethod
    def dataDirectory(cls):
        """
        Return the directory that contains test data.
        """
        return os.path.join(cls.__rootPath, "data")

    @classmethod
    def dataTestsDirectory(cls):
        """
        Return the directory that contains test data.
        """
        return os.path.join(cls.dataDirectory(), "tests")

    @classmethod
    def hasBin(cls, binName):
        """
        Return a boolean telling if the binary is under the search path.
        """
        return any(
            os.access(os.path.join(path, binName), os.X_OK)
            for path in os.environ["PATH"].split(os.pathsep)
        )

    @classmethod
    def setUpClass(cls):
        """
        Create the temporary directory used by the tests.
        """
        os.environ['KOMBI_TEMP_REMOTE_DIR'] = cls.tempDirectory()

    @classmethod
    def tearDownClass(cls):
        """
        Remove temporary files.
        """
        shutil.rmtree(cls.tempDirectory(), ignore_errors=True)
