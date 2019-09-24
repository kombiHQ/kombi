import os
import unittest
import tarfile
from zipfile import ZipFile
from ...BaseTestCase import BaseTestCase
from kombi.Task import Task
from kombi.Crawler.Fs import FsCrawler
from kombi.Task.Archive.PackTask import PackTaskUnsupportedTypeError

class PackTaskTest(BaseTestCase):
    """Test Pack task."""

    __targetZipDirectoryArchivePath = os.path.join(BaseTestCase.tempDirectory(), "testZipDirectoryArchive.zip")
    __targetGzArchivePath = os.path.join(BaseTestCase.tempDirectory(), "testZipArchive.gz")
    __targetZipMultipleArchive1Path = os.path.join(BaseTestCase.tempDirectory(), "testZipMultipleArchive1.zip")
    __targetZipMultipleArchive2Path = os.path.join(BaseTestCase.tempDirectory(), "testZipMultipleArchive2.zip")
    __targetTarArchivePath = os.path.join(BaseTestCase.tempDirectory(), "testTarArchive.tar")
    __targetTarGzArchivePath = os.path.join(BaseTestCase.tempDirectory(), "testTarGzArchive.tar.gz")
    __targetTgzArchivePath = os.path.join(BaseTestCase.tempDirectory(), "testTgzArchive.tgz")

    def testArchiveDirectory(self):
        """
        Test that can create an archive from a directory.
        """
        packTask = Task.create('pack')
        packTask.add(
            FsCrawler.createFromPath(os.path.join(BaseTestCase.dataTestsDirectory(), "glob")),
            self.__targetZipDirectoryArchivePath
        )

        # checking results
        result = packTask.output()
        self.assertEqual(len(result), 1)

        # checking contents
        with ZipFile(result[0].var('fullPath')) as f:
            self.assertListEqual(
                sorted(f.namelist()),
                sorted(
                   [
                        'glob/',
                        'glob/images/',
                        'glob/images/RND-TST-SHT_comp_compName_output_v010_tk.1001.exr',
                        'glob/images/RND-TST-SHT_lighting_beauty_sr.1001.exr',
                        'glob/images/RND_ass_lookdev_default_beauty_tt.1001.exr',
                        'glob/test.json',
                        'glob/test.txt'
                    ]
                )
            )

    def testArchiveZip(self):
        """
        Test that can create a zip (gz) archive.
        """
        packTask = Task.create('pack')
        packTask.add(
            FsCrawler.createFromPath(os.path.join(BaseTestCase.dataTestsDirectory(), "test.exr")),
            self.__targetGzArchivePath
        )
        packTask.add(
            FsCrawler.createFromPath(os.path.join(BaseTestCase.dataTestsDirectory(), "test.exr")),
            "{}[a|b|c|d.exr]".format(self.__targetGzArchivePath)
        )

        # checking results
        result = packTask.output()
        self.assertEqual(len(result), 1)

        # checking contents
        with ZipFile(result[0].var('fullPath')) as f:
            self.assertListEqual(
                sorted(f.namelist()),
                sorted(['test.exr', 'a/b/c/d.exr'])
            )

    def testMultipleArchives(self):
        """
        Test that can create multiple archives.
        """
        packTask = Task.create('pack')
        packTask.add(
            FsCrawler.createFromPath(os.path.join(BaseTestCase.dataTestsDirectory(), "test.exr")),
            self.__targetZipMultipleArchive1Path
        )
        packTask.add(
            FsCrawler.createFromPath(os.path.join(BaseTestCase.dataTestsDirectory(), "test.exr")),
            "{}[a|b|c|d.exr]".format(self.__targetZipMultipleArchive2Path)
        )
        # checking results
        result = packTask.output()
        self.assertEqual(len(result), 2)

        # checking contents
        with ZipFile(result[0].var('fullPath')) as f:
            self.assertListEqual(
                sorted(f.namelist()),
                sorted(['test.exr'])
            )

        with ZipFile(result[1].var('fullPath')) as f:
            self.assertListEqual(
                sorted(f.namelist()),
                sorted(['a/b/c/d.exr'])
            )

    def testArchiveTar(self):
        """
        Test that can create a tar archive.
        """
        packTask = Task.create('pack')
        packTask.add(
            FsCrawler.createFromPath(os.path.join(BaseTestCase.dataTestsDirectory(), "test.exr")),
            self.__targetTarArchivePath
        )
        packTask.add(
            FsCrawler.createFromPath(os.path.join(BaseTestCase.dataTestsDirectory(), "test.exr")),
            "{}[a|b|c|d.exr]".format(self.__targetTarArchivePath)
        )

        # checking results
        result = packTask.output()
        self.assertEqual(len(result), 1)

        # checking contents
        with tarfile.open(result[0].var('fullPath')) as f:
            self.assertListEqual(
                sorted(f.getnames()),
                sorted(['test.exr', 'a/b/c/d.exr'])
            )

    def testArchiveTarGz(self):
        """
        Test that can create a tar.gz archive.
        """
        packTask = Task.create('pack')
        packTask.add(
            FsCrawler.createFromPath(os.path.join(BaseTestCase.dataTestsDirectory(), "test.exr")),
            self.__targetTarGzArchivePath
        )
        packTask.add(
            FsCrawler.createFromPath(os.path.join(BaseTestCase.dataTestsDirectory(), "test.exr")),
            "{}[a|b|c|d.exr]".format(self.__targetTarGzArchivePath)
        )

        # checking results
        result = packTask.output()
        self.assertEqual(len(result), 1)

        # checking contents
        with tarfile.open(result[0].var('fullPath')) as f:
            self.assertListEqual(
                sorted(f.getnames()),
                sorted(['test.exr', 'a/b/c/d.exr'])
            )

    def testTgz(self):
        """
        Test that can create a tgz (tar.gz) archive.
        """
        packTask = Task.create('pack')
        packTask.add(
            FsCrawler.createFromPath(os.path.join(BaseTestCase.dataTestsDirectory(), "test.exr")),
            self.__targetTarGzArchivePath
        )

        # checking results
        result = packTask.output()
        self.assertEqual(len(result), 1)

        # checking contents
        with tarfile.open(result[0].var('fullPath')) as f:
            self.assertListEqual(
                sorted(f.getnames()),
                sorted(['test.exr'])
            )

    def testUnsupportedArchiveType(self):
        """
        Test the exception unsupported archive type.
        """
        crawler = FsCrawler.createFromPath(os.path.join(BaseTestCase.dataTestsDirectory(), "test.exr"))
        packTask = Task.create('pack')
        packTask.add(crawler, os.path.join(BaseTestCase.tempDirectory(), "testZipArchive.invalid"))
        self.assertRaises(PackTaskUnsupportedTypeError, packTask.output)

    @classmethod
    def tearDownClass(cls):
        """
        Remove temporary files.
        """
        if os.path.exists(cls.__targetZipDirectoryArchivePath):
            os.remove(cls.__targetZipDirectoryArchivePath)

        if os.path.exists(cls.__targetZipMultipleArchive1Path):
            os.remove(cls.__targetZipMultipleArchive1Path)

        if os.path.exists(cls.__targetZipMultipleArchive2Path):
            os.remove(cls.__targetZipMultipleArchive2Path)

        if os.path.exists(cls.__targetTgzArchivePath):
            os.remove(cls.__targetTgzArchivePath)

        if os.path.exists(cls.__targetGzArchivePath):
            os.remove(cls.__targetGzArchivePath)

        if os.path.exists(cls.__targetTarArchivePath):
            os.remove(cls.__targetTarArchivePath)

        if os.path.exists(cls.__targetTarGzArchivePath):
            os.remove(cls.__targetTarGzArchivePath)


if __name__ == "__main__":
    unittest.main()
