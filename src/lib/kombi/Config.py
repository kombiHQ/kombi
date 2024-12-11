import os
import sys
import json
import pathlib
import traceback

class Config(object):
    """
    This class can be used to store arbitrary config data.
    """
    __configBaseDirectoryEnv = os.environ.get('KOMBI_CONFIG_DIRECTORY')

    def __init__(self, name):
        """
        Initializes a configuration name.
        """
        assert isinstance(name, str), 'config name needs to be defined as string'

        self.__name = name
        self.__filePath = None
        self.__data = {}

        self.__parse()

    def name(self):
        """
        Return the config name.
        """
        return self.__name

    def setValue(self, key, value, serialize=True):
        """
        Set the value for the input key.
        """
        assert isinstance(key, str), 'key needs to be defined as string'
        self.__data[key] = value

        if serialize:
            self.__serialize()

    def setValues(self, **kwargs):
        """
        Set multiple pairs of key/value.
        """
        for key, value in kwargs.items():
            self.setValue(key, value, serialize=False)

        self.__serialize()

    def hasKey(self, key):
        """
        Return a boolean telling if the input key exists under the config.
        """
        return key in self.__data

    def keys(self):
        """
        Return all keys stored under the config.
        """
        return self.__data.keys()

    def value(self, key):
        """
        Return the value for the input key.
        """
        return self.__data[key]

    def clear(self):
        """
        Purge all data under the config.
        """
        self.__data = {}
        self.__serialize()

    def filePath(self):
        """
        Return the file path for the config.
        """
        if self.__filePath is None:
            configBaseDirectory = None
            if self.__configBaseDirectoryEnv:
                configBaseDirectory = pathlib.Path(self.__configBaseDirectoryEnv)
            else:
                configBaseDirectory = self.__defaultKombiConfigBaseDirectory()

            os.makedirs(configBaseDirectory, exist_ok=True)
            self.__filePath = configBaseDirectory / f'{self.name()}.json'

        return self.__filePath

    def __parse(self):
        """
        Load the config data.
        """
        if not os.path.exists(self.filePath()):
            return

        with open(self.filePath()) as f:
            try:
                self.__data = json.load(f)
            except Exception:
                self.__data = {}
                sys.stderr.write(f'Failed to load config: {self.filePath()}\n')
                sys.stderr.flush()
                traceback.print_exc()

    def __serialize(self):
        """
        Serialize the config data.
        """
        with open(self.filePath(), 'w') as f:
            json.dump(self.__data, f, indent=4)

    @staticmethod
    def __defaultKombiConfigBaseDirectory():
        """
        Return the default config base directory when KOMBI_CONFIG_DIRECTORY is not defined.

        Based on: https://stackoverflow.com/questions/19078969/python-getting-appdata-folder-in-a-cross-platform-way
        """
        home = pathlib.Path.home()

        applicationData = None
        if sys.platform == 'win32':
            applicationData = home / 'AppData/Roaming'
        elif os.name == 'posix':
            applicationData = home / '.local/share'
        elif sys.platform == 'darwin':
            applicationData = home / 'Library/Application Support'

        assert applicationData

        return applicationData / 'kombi'
