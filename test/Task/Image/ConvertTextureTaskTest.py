import os
import unittest
from ...BaseTestCase import BaseTestCase
from kombi.Task import Task
from kombi.Element.Fs import FsElement

class ConvertTextureTaskTest(BaseTestCase):
    """
    Test ConvertTexture task.
    """

    __sourcePath = os.path.join(BaseTestCase.dataTestsDirectory(), "test.png")
    __targetPath = os.path.join(BaseTestCase.tempDirectory(), "testToDelete.tx")

    @unittest.skipIf(not BaseTestCase.hasBin(os.environ.get('KOMBI_MAKETX_EXECUTABLE', 'maketx')), 'maketx not found in the search path')
    def testConvertTexture(self):
        """
        Test that the ConvertTexture task works properly.
        """
        element = FsElement.createFromPath(self.__sourcePath)
        convertTask = Task.create('convertTexture')
        convertTask.setOption('maketxArgs', '-u --unpremult --oiio')
        convertTask.add(element, self.__targetPath)
        result = convertTask.output()

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].var('filePath'), self.__targetPath)
        self.assertTrue(os.path.exists(self.__targetPath))


if __name__ == "__main__":
    unittest.main()
