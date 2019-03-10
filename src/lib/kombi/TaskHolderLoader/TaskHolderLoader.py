import os
import uuid
from ..TaskHolder import TaskHolder

class TaskHolderLoaderError(Exception):
    """Task Holder Loader Error."""

class TaskHolderLoaderNotRegisteredError(TaskHolderLoaderError):
    """Task Holder Loader Not Registered Error."""

class TaskHolderLoaderInvalidConfigError(TaskHolderLoaderError):
    """Task Holder Loader Invalid Config Error."""

class TaskHolderLoader(object):
    """
    Abstracted task holders loader.
    """

    __registered = {}

    def __init__(self):
        """
        Create a config loader.
        """
        self.__taskHolders = []

    def loadFromDirectory(self, directory):
        """
        Load the configuration from inside of a directory by looking for configuration files supported by the loaders.
        """
        # making sure it is a valid directory
        if not (os.path.exists(directory) and os.path.isdir(directory)):
            raise TaskHolderLoaderInvalidConfigError(
                'Invalid directory "{0}"!'.format(directory)
            )

        # collecting all files under the directory
        for fileName in os.listdir(directory):
            filePath = os.path.join(directory, fileName)
            if not os.path.isfile(filePath):
                continue

            # loading config
            ext = os.path.splitext(filePath)[-1][1:]
            if ext in self.registeredNames():
                self.loadFromFile(filePath)

    def loadFromFile(self, filePath):
        """
        Load the task holder from a file.
        """
        # making sure it's a valid file
        if not (os.path.exists(filePath) and os.path.isfile(filePath)):
            raise TaskHolderLoaderInvalidConfigError(
                'Invalid file "{0}"!'.format(filePath)
            )

        # checking if we have a loader for the file
        ext = os.path.splitext(filePath)[-1][1:]
        if ext not in self.registeredNames():
            raise TaskHolderLoaderInvalidConfigError(
                "Cannot find a loader for: {}".format(filePath)
            )

        # loading task holder
        fileTaskHolder = self.create(ext)
        with open(filePath) as (f):
            try:
                fileTaskHolder.load(
                    fileTaskHolder.parse(f.read()),
                    {
                        'configDirectory': os.path.dirname(filePath),
                        'contextConfig': filePath,
                        'sessionId': str(uuid.uuid4())
                    }
                )
            except Exception as err:
                raise TaskHolderLoaderInvalidConfigError(
                    '{}\n ^--- {} while loading file: {}'.format(
                        str(err),
                        err.__class__.__name__,
                        filePath
                    )
                )

        for loadedTaskHolder in fileTaskHolder.taskHolders():
            self.addTaskHolder(loadedTaskHolder)

    def addTaskHolder(self, taskHolder):
        """
        Add a task holder to the config loader.
        """
        assert (isinstance(taskHolder, TaskHolder)), \
            "Invalid task holder object"

        self.__taskHolders.append(taskHolder)

    def taskHolders(self):
        """
        Return a list of task holders associated with the config loader.
        """
        return self.__taskHolders

    def load(self, contents, contextVars={}):
        """
        For re-implementation: Should load the content to the taskholder.
        """
        raise NotImplementedError

    @classmethod
    def parse(cls, contents):
        """
        For re-implementation: should parse the contents to a python data-structure.
        """
        raise NotImplementedError

    @staticmethod
    def register(name, taskHolderLoader):
        """
        Register a task holder loader type.
        """
        assert issubclass(taskHolderLoader, TaskHolderLoader), \
            "Invalid task holder loader class!"

        TaskHolderLoader.__registered[name] = taskHolderLoader

    @staticmethod
    def registeredNames():
        """
        Return a list of registered task holder loaders.
        """
        return list(TaskHolderLoader.__registered.keys())

    @staticmethod
    def create(taskHolderLoaderName, *args, **kwargs):
        """
        Create a task holder loader object.
        """
        if taskHolderLoaderName not in TaskHolderLoader.__registered:
            raise TaskHolderLoaderNotRegisteredError(
                'Task holder loader is not registered: "{0}"'.format(
                    taskHolderLoaderName
                )
            )

        return TaskHolderLoader.__registered[taskHolderLoaderName](
            *args,
            **kwargs
        )
