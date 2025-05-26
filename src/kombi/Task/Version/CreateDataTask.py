import os
import getpass
import json
import shutil
from ..Task import Task, TaskError

class CreateDataTaskError(TaskError):
    """Generic Create Data Task Error."""

class CreateDataTaskFileNotUnderDataDirectoryError(CreateDataTaskError):
    """Create Data File Not Under Data Directory Error."""

class CreateDataTaskMetadataNotFoundError(CreateDataTaskError):
    """Create Data Metadata Not Found Error."""

class CreateDataTaskInvalidInfoError(CreateDataTaskError):
    """Create Data Invalid Info Error."""

class CreateDataTask(Task):
    """
    ABC for creating data.
    """

    __dataDirectoryName = "data"

    def __init__(self, *args, **kwargs):
        """
        Create data.
        """
        super(CreateDataTask, self).__init__(*args, **kwargs)
        self.__files = {}
        self.__info = {}
        self.__loadedStaticData = False

    def copyFile(self, sourceFile, targetFile):
        """
        Auxiliary method used to copy a file by creating any necessary directories.
        """
        self.makeDirs(os.path.dirname(targetFile))

        shutil.copyfile(sourceFile, targetFile)

    def makeDirs(self, targetPath):
        """
        Auxiliary method used to create directories.
        """
        if not os.path.exists(targetPath):
            try:
                os.makedirs(targetPath)
            except OSError:
                pass

    def dataPath(self):
        """
        Return the path where the data should be stored.
        """
        return os.path.join(self.rootPath(), CreateDataTask.__dataDirectoryName)

    def rootPath(self):
        """
        Return the root path where the data directory and json files should exist.
        """
        return self.__rootPath

    def configDirectory(self):
        """
        Return the path about the location for the configuration used by kombi.
        """
        return self.__configDirectory

    def addInfo(self, key, value):
        """
        Associate an info to the published version.

        This information is used to write "info.json".
        """
        self.__info[key] = value

    def info(self, key):
        """
        Return value of given info.
        """
        if key not in self.__info:
            raise CreateDataTaskInvalidInfoError(
                'Info not found "{}"'.format(key)
            )

        return self.__info[key]

    def infoNames(self):
        """
        Return a list of info names that currently exist.
        """
        return list(self.__info.keys())

    def addFile(self, filePath, metadata=None):
        """
        Add a published file that is under the 'data' directory.

        This information is used to write "data.json" where metadata information
        can be associated with the file through metadata parameter
        passed as dictionary.
        """
        # making sure the file is under the data directory
        if not filePath.startswith(self.dataPath() + os.sep):
            raise CreateDataTaskFileNotUnderDataDirectoryError(
                'File "{0}" is not under data directory "{1}"'.format(
                    filePath,
                    self.dataPath()
                )
            )

        if metadata is None:
            metadata = {}

        assert isinstance(metadata, dict), "metadata needs to be a dict or None"

        # making metadata immutable
        metadata = dict(metadata)

        # querying the stats about the file
        fileStat = os.stat(filePath)

        # getting file size
        metadata['size'] = fileStat.st_size

        # adding type based on the file ext when it's not defined
        if 'type' not in metadata:
            metadata['type'] = os.path.splitext(filePath)[-1][1:]

        self.__files[filePath] = metadata

    def files(self):
        """
        Return a list of published file names under data.
        """
        return list(self.__files.keys())

    def fileMetadata(self, filePath):
        """
        Return the metadata for the input file path.
        """
        if filePath in self.__files:
            # we don't want to share implicitly the metadata object.
            return dict(self.__files[filePath])

        raise CreateDataTaskMetadataNotFoundError(
            'Could not find metadata for the file "{0}"'.format(filePath)
        )

    def updateInfo(self):
        """
        Update info.json file with new file data.
        """
        infoJsonFilePath = os.path.join(self.rootPath(), "info.json")
        infoDict = {}
        if os.path.exists(infoJsonFilePath):
            with open(infoJsonFilePath, 'r') as jsonOutFile:
                infoDict = json.load(jsonOutFile)

        totalSize = 0
        for fileName, metadata in self.__files.items():
            totalSize += metadata['size']

        self.addInfo('size', infoDict.get('size', 0) + totalSize)
        self.addInfo('user', os.environ.get("KOMBI_USER", getpass.getuser()))

        self.__info.update(infoDict)
        # writing info json file
        with open(infoJsonFilePath, 'w') as jsonOutFile:
            json.dump(self.__info, jsonOutFile, indent=4, sort_keys=True)

    def updateData(self):
        """
        Update data.json file with new files.
        """
        dataJsonFilePath = os.path.join(self.rootPath(), "data.json")
        filesData = {}
        if os.path.exists(dataJsonFilePath):
            with open(dataJsonFilePath, 'r') as jsonOutFile:
                filesData = json.load(jsonOutFile)

        for filePath, metadata in self.__files.items():
            relativePath = filePath[len(self.rootPath()) + 1:]
            filesData[relativePath] = metadata

        with open(dataJsonFilePath, 'w') as jsonOutFile:
            json.dump(filesData, jsonOutFile, indent=4, sort_keys=True)

    def add(self, *args, **kwargs):
        """
        Cache the static information about the first element you add.
        """
        super(CreateDataTask, self).add(*args, **kwargs)
        self.__loadStaticData()

    def _perform(self):
        """
        Perform the task.
        """
        self.__writeEnv()
        self.__copyKombiConfig()
        self.updateInfo()
        self.updateData()

        return super(CreateDataTask, self)._perform()

    def __writeEnv(self):
        """
        Write env.json file.
        """
        envJsonFilePath = os.path.join(self.rootPath(), "env.json")
        if os.path.exists(envJsonFilePath):
            return
        with open(envJsonFilePath, 'w') as jsonOutFile:
            json.dump(dict(os.environ), jsonOutFile, indent=4, sort_keys=True)

    def __copyKombiConfig(self):
        """
        Copy the configuration used by kombi to the current version.
        """
        configDirectory = os.path.join(self.rootPath(), "kombiConfig")
        if os.path.exists(configDirectory):
            return
        shutil.copytree(
            self.configDirectory(),
            configDirectory
        )

    def __loadStaticData(self):
        """
        Load static information.
        """
        if self.__loadedStaticData or not self.elements():
            return

        self.__loadedStaticData = True

        element = self.elements()[0]
        self.__rootPath = self.target(element)
        self.__configDirectory = element.var('configDirectory')
