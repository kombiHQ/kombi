import unittest
import os
from ...BaseTestCase import BaseTestCase
from kombi.Task import Task
from kombi.Template import Template
from kombi.Element.Fs import FsElement, DirectoryElement
from kombi.Element.Fs.Image import ExrElement
from kombi.Element.Fs.Ascii import JsonElement, TxtElement

class GlobTaskTest(BaseTestCase):
    """Test Glob task."""

    __globFiles = {
        'exr': [
            'RND-TST-SHT_comp_compName_output_v010_tk.1001.exr',
            'RND_ass_lookdev_default_beauty_tt.1001.exr',
            'RND-TST-SHT_lighting_beauty_sr.1001.exr'
        ],
        'json': [
            'test.json'
        ],
        'txt': [
            'test.txt'
        ],
        'directory': [
            'images'
        ]
    }

    def testGlobSpecficFiles(self):
        """
        Test that the glob task looking for specific exr files.
        """
        element = FsElement.createFromPath(
            os.path.join(BaseTestCase.dataTestsDirectory(), "glob", "test.json")
        )

        globTask = Task.create('glob')
        globTask.add(
            element,
            Template("!kt (dirname {filePath})/**/*.exr").valueFromElement(element)
        )
        result = globTask.output()
        self.assertEqual(len(result), len(self.__globFiles['exr']))

        for resultElement in result:
            self.assertIsInstance(resultElement, ExrElement)
            self.assertIn(resultElement.var('baseName'), self.__globFiles['exr'])

    def testGlobAll(self):
        """
        Test that the glob task find all files & directories.
        """
        element = FsElement.createFromPath(
            os.path.join(BaseTestCase.dataTestsDirectory(), "glob", "test.json")
        )

        globTask = Task.create('glob')
        globTask.add(
            element,
            Template("!kt (dirname {filePath})/**/*").valueFromElement(element)
        )
        result = globTask.output()
        self.assertEqual(
            len(result),
            len(self.__globFiles['exr']) + len(self.__globFiles['json']) + len(self.__globFiles['txt']) + len(self.__globFiles['directory'])
        )

        for resultElement in result:
            baseType = 'directory' if 'ext' not in resultElement.varNames() else resultElement.var('ext')
            if baseType == 'exr':
                ElementType = ExrElement
            elif baseType == 'json':
                ElementType = JsonElement
            elif baseType == 'txt':
                ElementType = TxtElement
            else:
                baseType = 'directory'
                ElementType = DirectoryElement

            self.assertIsInstance(resultElement, ElementType)
            self.assertIn(resultElement.var('baseName'), self.__globFiles[baseType])

    def testGlobSkipDuplicated(self):
        """
        Test that the glob task with the option skip duplicated enabled (default).
        """
        element1 = FsElement.createFromPath(
            os.path.join(BaseTestCase.dataTestsDirectory(), "glob", "test.json")
        )

        element2 = FsElement.createFromPath(
            os.path.join(BaseTestCase.dataTestsDirectory(), "glob", "test.txt")
        )

        globTask = Task.create('glob')
        globTask.add(
            element1,
            Template("!kt (dirname {filePath})/**/*.exr").valueFromElement(element1)
        )
        globTask.add(
            element2,
            Template("!kt (dirname {filePath})/images/*.exr").valueFromElement(element2)
        )
        result = globTask.output()
        self.assertEqual(len(result), len(self.__globFiles['exr']))

        for resultElement in result:
            self.assertIsInstance(resultElement, ExrElement)
            self.assertIn(resultElement.var('baseName'), self.__globFiles['exr'])

    def testGlobDontSkipDuplicated(self):
        """
        Test that the glob task with he option skip duplicated disabled.
        """
        element1 = FsElement.createFromPath(
            os.path.join(BaseTestCase.dataTestsDirectory(), "glob", "test.json")
        )

        element2 = FsElement.createFromPath(
            os.path.join(BaseTestCase.dataTestsDirectory(), "glob", "test.txt")
        )

        globTask = Task.create('glob')
        globTask.setOption('skipDuplicated', False)

        globTask.add(
            element1,
            Template("!kt (dirname {filePath})/**/*.exr").valueFromElement(element1)
        )
        globTask.add(
            element2,
            Template("!kt (dirname {filePath})/images/*.exr").valueFromElement(element2)
        )

        result = globTask.output()
        self.assertEqual(len(result), len(self.__globFiles['exr']) * 2)

        for resultElement in result:
            self.assertIsInstance(resultElement, ExrElement)
            self.assertIn(resultElement.var('baseName'), self.__globFiles['exr'])


if __name__ == "__main__":
    unittest.main()
