import os
import io
import unittest
import tempfile
from fnmatch import fnmatch
from ....BaseTestCase import BaseTestCase
from kombi.InfoCrate.Fs import FsInfoCrate
from kombi.TaskHolder.Loader import JsonLoader
from kombi.TaskWrapper import TaskWrapper
from kombi.Task import Task
from kombi.InfoCrate.Fs.Image import JpgInfoCrate, ExrInfoCrate
from kombi.TaskHolder.Dispatcher import Dispatcher

class LocalDispatcherTest(BaseTestCase):
    """Test for the local dispatcher."""

    __jsonConfig = os.path.join(BaseTestCase.dataTestsDirectory(), 'config', 'dispatcherTest.json')
    __output = """
        copy output (execution * seconds):
          - nukeRender(*/RND-TST-SHT_comp_compName_output_v010_tk.1001.exr)
          - shotRender(*/RND-TST-SHT_lighting_beauty_sr.1001.exr)
          - turntable(*/RND_ass_lookdev_default_beauty_tt.1001.exr)
          - testInfoCrate(*/testSeq.0001.exr)
          - testInfoCrate(*/testSeq.0002.exr)
          - testInfoCrate(*/testSeq.0003.exr)
          - testInfoCrate(*/testSeq.0004.exr)
          - testInfoCrate(*/testSeq.0005.exr)
          - testInfoCrate(*/testSeq.0006.exr)
          - testInfoCrate(*/testSeq.0007.exr)
          - testInfoCrate(*/testSeq.0008.exr)
          - testInfoCrate(*/testSeq.0009.exr)
          - testInfoCrate(*/testSeq.0010.exr)
          - testInfoCrate(*/testSeq.0011.exr)
          - testInfoCrate(*/testSeq.0012.exr)
          - testInfoCrate(*/test_0001.exr)
        done
        sequenceThumbnail output (execution * seconds):
          - jpg(*/testSeq.jpg)
        done
    """

    def testConfig(self):
        """
        Test that you can run tasks through a config file properly.
        """
        taskHolderLoader = JsonLoader()
        taskHolderLoader.loadFromFile(self.__jsonConfig)
        infoCrates = FsInfoCrate.createFromPath(BaseTestCase.dataTestsDirectory()).glob()
        temporaryDir = tempfile.mkdtemp()

        dispacher = Dispatcher.create("local")
        outputStream = io.StringIO()
        dispacher.setStdout(outputStream)
        dispacher.setOption(
            'enableVerboseOutput',
            False
        )

        dispacher.setOption(
            'awaitExecution',
            True
        )

        for taskHolder in taskHolderLoader.taskHolders():
            taskHolder.addVar(
                'temporaryDir',
                temporaryDir,
                True
            )
            dispacher.dispatch(taskHolder, infoCrates)

        createdInfoCrates = FsInfoCrate.createFromPath(temporaryDir).glob()
        exrInfoCrates = list(filter(lambda x: isinstance(x, ExrInfoCrate), createdInfoCrates))
        self.assertEqual(len(exrInfoCrates), 16)

        jpgInfoCrates = list(filter(lambda x: isinstance(x, JpgInfoCrate), createdInfoCrates))
        self.assertEqual(len(jpgInfoCrates), 1)

        output = outputStream.getvalue().replace('\r\n', '\n').split('\n')
        prefixSize = None
        for index, line in enumerate(self.__output.split('\n')[1:-1]):
            if prefixSize is None:
                prefixSize = len(line) - len(line.lstrip())

            line = line[prefixSize:]
            outputLine = output[index].replace('\\', '/')
            if not fnmatch(outputLine, line):
                self.assertEqual(outputLine, line)

        self.cleanup(exrInfoCrates + jpgInfoCrates)

    def cleanup(self, infoCrates):
        """
        Remove the data that was copied.
        """
        removeTask = Task.create('remove')
        for infoCrate in infoCrates:
            removeTask.add(infoCrate, infoCrate.var("filePath"))
        wrapper = TaskWrapper.create('python')
        wrapper.setOption('user', '')
        wrapper.run(removeTask)


if __name__ == "__main__":
    unittest.main()
