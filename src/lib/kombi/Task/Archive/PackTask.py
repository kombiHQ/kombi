import os
from collections import OrderedDict
from zipfile import ZipFile, ZIP_DEFLATED, ZIP_STORED
from tarfile import TarFile
from ..Task import Task, TaskError
from ...Element.Fs.FsElement import FsElement
from ...Element.Fs.DirectoryElement import DirectoryElement

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
        for taskElement in self.elements():

            allElements = []
            # in case of directory element we glob for the contents
            if isinstance(taskElement, DirectoryElement):
                allElements += taskElement.glob()
            else:
                allElements.append(taskElement)

            filePath = self.target(taskElement)

            # resolving the internal path for the elements
            for element in allElements:
                internalArchivePath = None

                # elements based on directory elements the internal path is relative to source directory element
                if isinstance(taskElement, DirectoryElement):
                    internalArchivePath = element.var('fullPath')[len(taskElement.var('fullPath')) - len(taskElement.var('baseName')):]

                # elements containing a custom internal path that can be declared as part of the target path,
                # for instance: test.zip[a/b/c/file.ext]
                elif filePath.endswith(']') and filePath.count('[') == 1:
                    filePath, internalArchivePath = filePath[:-1].split('[')
                    internalArchivePath = internalArchivePath.replace('|', '/')

                # otherwise the internal path is the base name of the element
                else:
                    internalArchivePath = element.var('baseName')

                if filePath not in archive:
                    archive[filePath] = []
                archive[filePath].append(
                    {
                        'element': element,
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

        return list(map(FsElement.createFromPath, archive.keys()))

    def __archiveTar(self, archiveFilePath, archiveItems, compressTar):
        """
        Create a tar archive.
        """
        compress = compressTar if self.option('compress') is None else self.option('compress')
        archiveMode = 'w:gz' if compress else 'w'

        with TarFile.open(archiveFilePath, archiveMode) as archiveFile:
            for archiveItem in archiveItems:
                archiveFile.add(archiveItem['element'].var('fullPath'), archiveItem['internalPath'])

    def __archiveZip(self, archiveFilePath, archiveItems):
        """
        Create a zip archive.
        """
        archiveMode = ZIP_DEFLATED if self.option('compress') else ZIP_STORED

        with ZipFile(archiveFilePath, 'w', compression=archiveMode, allowZip64=True) as archiveFile:
            for archiveItem in archiveItems:
                archiveFile.write(archiveItem['element'].var('fullPath'), archiveItem['internalPath'])


# registering task
Task.register(
    'pack',
    PackTask
)
