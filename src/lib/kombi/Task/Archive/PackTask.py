import os
from collections import OrderedDict
from zipfile import ZipFile, ZIP_DEFLATED, ZIP_STORED
from tarfile import TarFile
from ..Task import Task, TaskError
from ...Crawler.Fs.FsCrawler import FsCrawler
from ...Crawler.Fs.DirectoryCrawler import DirectoryCrawler

class PackTaskUnsupportedTypeError(TaskError):
    """Pack Task Unsupported Type Error."""

class PackTask(Task):
    """
    Task used for creating archives in tar, zip (or gz) and tar.gz (or tgz).

    You can use this task to archive entire directories or/and specific files.

    Optionality: In case you want to define a custom path for each file inside
    of the archive you can do that by defining the new name inside of "[]" after
    the archive file name where the internal levels inside of the archive should
    be represented by "|". For instance defining a custom internal path
    for the target:
        /a/b/c/test.zip[a|b|c|d.exr]
        /a/b/c/test.zip[a|b|foo.txt]
    """

    def __init__(self, *args, **kwargs):
        """
        Create a Pack task.
        """
        super(PackTask, self).__init__(*args, **kwargs)

        # option telling if the archive should be compressed.
        # None means this option should be driven per archive type.
        self.setOption('compress', None)

    def _perform(self):
        """
        Perform the task.
        """
        archive = OrderedDict()
        for taskCrawler in self.crawlers():

            allCrawlers = []
            # in case of directory crawler we glob for the contents
            if isinstance(taskCrawler, DirectoryCrawler):
                allCrawlers += taskCrawler.glob()
            else:
                allCrawlers.append(taskCrawler)

            filePath = self.target(taskCrawler)

            # resolving the internal path for the crawlers
            for crawler in allCrawlers:
                internalArchivePath = None

                # crawlers based on directory crawlers the internal path is relative to source directory crawler
                if isinstance(taskCrawler, DirectoryCrawler):
                    internalArchivePath = crawler.var('fullPath')[len(taskCrawler.var('fullPath')) - len(taskCrawler.var('baseName')):]

                # crawlers containing a custom internal path that can be declared as part of the target path,
                # for instance: test.zip[a/b/c/file.ext]
                elif filePath.endswith(']') and filePath.count('[') == 1:
                    filePath, internalArchivePath = filePath[:-1].split('[')
                    internalArchivePath = internalArchivePath.replace('|', '/')

                # otherwise the internal path is the base name of the crawler
                else:
                    internalArchivePath = crawler.var('baseName')

                if filePath not in archive:
                    archive[filePath] = []
                archive[filePath].append(
                    {
                        'crawler': crawler,
                        'internalPath': internalArchivePath
                    }
                )

        # creating archives
        for archiveFilePath, archiveItems in archive.items():
            archiveName = os.path.basename(archiveFilePath).lower()

            # tar archive
            if archiveName.endswith('.tar') or archiveName.endswith('.tar.gz') or archiveName.endswith('.tgz'):
                compressTar = archiveName.endswith('.tgz') or archiveName.endswith('.tar.gz')
                self.__archiveTar(archiveFilePath, archiveItems, compressTar)

            # zip archive
            elif archiveName.endswith('.zip') or archiveName.endswith('.gz'):
                self.__archiveZip(archiveFilePath, archiveItems)
            else:
                raise PackTaskUnsupportedTypeError(
                    'Unsupported archive type: {}'.format(archiveName)
                )

        return list(map(FsCrawler.createFromPath, archive.keys()))

    def __archiveTar(self, archiveFilePath, archiveItems, compressTar):
        """
        Create a tar archive.
        """
        compress = compressTar if self.option('compress') is None else self.option('compress')
        archiveMode = 'w:gz' if compress else 'w'

        with TarFile.open(archiveFilePath, archiveMode) as archiveFile:
            for archiveItem in archiveItems:
                archiveFile.add(archiveItem['crawler'].var('fullPath'), archiveItem['internalPath'])

    def __archiveZip(self, archiveFilePath, archiveItems):
        """
        Create a zip archive.
        """
        archiveMode = ZIP_DEFLATED if self.option('compress') else ZIP_STORED

        with ZipFile(archiveFilePath, 'w', compression=archiveMode, allowZip64=True) as archiveFile:
            for archiveItem in archiveItems:
                archiveFile.write(archiveItem['crawler'].var('fullPath'), archiveItem['internalPath'])


# registering task
Task.register(
    'pack',
    PackTask
)
