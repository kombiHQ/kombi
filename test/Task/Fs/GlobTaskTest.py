import unittest
import os
from ...BaseTestCase import BaseTestCase
from kombi.Task import Task
from kombi.Template import Template
from kombi.InfoCrate.Fs import FsInfoCrate, DirectoryInfoCrate
from kombi.InfoCrate.Fs.Image import ExrInfoCrate
from kombi.InfoCrate.Fs.Ascii import JsonInfoCrate, TxtInfoCrate

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
        infoCrate = FsInfoCrate.createFromPath(
            os.path.join(BaseTestCase.dataTestsDirectory(), "glob", "test.json")
        )

        globTask = Task.create('glob')
        globTask.add(
            infoCrate,
            Template("(dirname {filePath})/**/*.exr").valueFromInfoCrate(infoCrate)
        )
        result = globTask.output()
        self.assertEqual(len(result), len(self.__globFiles['exr']))

        for resultInfoCrate in result:
            self.assertIsInstance(resultInfoCrate, ExrInfoCrate)
            self.assertIn(resultInfoCrate.var('baseName'), self.__globFiles['exr'])

    def testGlobAll(self):
        """
        Test that the glob task find all files & directories.
        """
        infoCrate = FsInfoCrate.createFromPath(
            os.path.join(BaseTestCase.dataTestsDirectory(), "glob", "test.json")
        )

        globTask = Task.create('glob')
        globTask.add(
            infoCrate,
            Template("(dirname {filePath})/**/*").valueFromInfoCrate(infoCrate)
        )
        result = globTask.output()
        self.assertEqual(
            len(result),
            len(self.__globFiles['exr']) + len(self.__globFiles['json']) + len(self.__globFiles['txt']) + len(self.__globFiles['directory'])
        )

        for resultInfoCrate in result:
            baseType = 'directory' if 'ext' not in resultInfoCrate.varNames() else resultInfoCrate.var('ext')
            if baseType == 'exr':
                InfoCrateType = ExrInfoCrate
            elif baseType == 'json':
                InfoCrateType = JsonInfoCrate
            elif baseType == 'txt':
                InfoCrateType = TxtInfoCrate
            else:
                baseType = 'directory'
                InfoCrateType = DirectoryInfoCrate

            self.assertIsInstance(resultInfoCrate, InfoCrateType)
            self.assertIn(resultInfoCrate.var('baseName'), self.__globFiles[baseType])

    def testGlobSkipDuplicated(self):
        """
        Test that the glob task with the option skip duplicated enabled (default).
        """
        infoCrate1 = FsInfoCrate.createFromPath(
            os.path.join(BaseTestCase.dataTestsDirectory(), "glob", "test.json")
        )

        infoCrate2 = FsInfoCrate.createFromPath(
            os.path.join(BaseTestCase.dataTestsDirectory(), "glob", "text.txt")
        )

        globTask = Task.create('glob')
        globTask.add(
            infoCrate1,
            Template("(dirname {filePath})/**/*.exr").valueFromInfoCrate(infoCrate1)
        )
        globTask.add(
            infoCrate2,
            Template("(dirname {filePath})/images/*.exr").valueFromInfoCrate(infoCrate2)
        )
        result = globTask.output()
        self.assertEqual(len(result), len(self.__globFiles['exr']))

        for resultInfoCrate in result:
            self.assertIsInstance(resultInfoCrate, ExrInfoCrate)
            self.assertIn(resultInfoCrate.var('baseName'), self.__globFiles['exr'])

    def testGlobDontSkipDuplicated(self):
        """
        Test that the glob task with he option skip duplicated disabled.
        """
        infoCrate1 = FsInfoCrate.createFromPath(
            os.path.join(BaseTestCase.dataTestsDirectory(), "glob", "test.json")
        )

        infoCrate2 = FsInfoCrate.createFromPath(
            os.path.join(BaseTestCase.dataTestsDirectory(), "glob", "text.txt")
        )

        globTask = Task.create('glob')
        globTask.setOption('skipDuplicated', False)

        globTask.add(
            infoCrate1,
            Template("(dirname {filePath})/**/*.exr").valueFromInfoCrate(infoCrate1)
        )
        globTask.add(
            infoCrate2,
            Template("(dirname {filePath})/images/*.exr").valueFromInfoCrate(infoCrate2)
        )

        result = globTask.output()
        self.assertEqual(len(result), len(self.__globFiles['exr']) * 2)

        for resultInfoCrate in result:
            self.assertIsInstance(resultInfoCrate, ExrInfoCrate)
            self.assertIn(resultInfoCrate.var('baseName'), self.__globFiles['exr'])


if __name__ == "__main__":
    unittest.main()
