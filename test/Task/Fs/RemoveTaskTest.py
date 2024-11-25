import unittest
import os
from ...BaseTestCase import BaseTestCase
from kombi.Task import Task
from kombi.Element.Fs import FsElement

class RemoveTaskTest(BaseTestCase):
    """Test Remove task."""

    __path = os.path.join(BaseTestCase.tempDirectory(), "toRemove.exr")

    @classmethod
    def setUpClass(cls):
        """
        Create a file to remove in the test.
        """
        open(cls.__path, 'w').close()

    def testRemove(self):
        """
        Test that the remove task works properly.
        """
        element = FsElement.createFromPath(self.__path)
        removeTask = Task.create('remove')
        removeTask.add(element, self.__path)
        result = removeTask.output()
        self.assertEqual(len(result), 1)
        element = result[0]
        self.assertFalse(os.path.isfile(element.var("filePath")))


if __name__ == "__main__":
    unittest.main()
