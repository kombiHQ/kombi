import os
import sys
import json
import pathlib
import traceback
from .KombiError import KombiError

class ConfigKeyError(KombiError):
    """Config Key Error."""

class _ConfigSentinelValue:
    """Config sentinel value."""

class Config(object):
    """
    This class can be used to store arbitrary config data.
    """
    __sentinelValue = _ConfigSentinelValue()
    __configBaseDirectoryEnv = os.environ.get('KOMBI_CONFIG_DIRECTORY')

    def __init__(self, name, group=''):
        """
        Initializes a configuration name.
        """
        assert isinstance(name, str), 'config name needs to be defined as string'

        self.__name = name
        self.__group = group
        self.__filePath = None
        self.__data = {}

        self.__parse()

    def name(self):
        """
        Return the config name.
        """
        return self.__name

    def group(self):
        """
        Return the group associated with the config.

        This information when defined is used to store the config in a sub-directory (named following the group name).
        """
        return self.__group

    def setValue(self, key, value, serialize=True):
        """
        Set the value for the input key.
        """
        assert isinstance(key, str), 'key needs to be defined as string'
        self.__data[key] = value

        if serialize:
            self.serialize()

    def setValues(self, **kwargs):
        """
        Set multiple pairs of key/value.
        """
        for key, value in kwargs.items():
            self.setValue(key, value, serialize=False)

        self.serialize()

    def hasKey(self, key):
        """
        Return a boolean telling if the input key exists under the config.
        """
        return key in self.__data

    def removeKey(self, key, serialize=True):
        """
        Remove the key from the config.
        """
        if key not in self.__data:
            return

        del self.__data[key]
        if serialize:
            self.serialize()

    def keys(self):
        """
        Return all keys stored under the config.
        """
        return self.__data.keys()

    def value(self, key, defaultValue=__sentinelValue):
        """
        Return the value for the input key.

        In case a defaultValue is not specified this method will raise the
        exception ConfigKeyError when the key does not exist.
        """
        if key in self.__data:
            return self.__data[key]

        if defaultValue is self.__sentinelValue:
            raise ConfigKeyError(
                'Invalid key "{}"'.format(key)
            )
        else:
            return defaultValue

    def clear(self):
        """
        Purge all data under the config.
        """
        self.__data = {}
        self.serialize()

    def filePath(self):
        """
        Return the file path for the config.
        """
        if self.__filePath is None:
            configDirectory = None
            if self.__configBaseDirectoryEnv:
                configDirectory = pathlib.Path(self.__configBaseDirectoryEnv)
            else:
                configDirectory = self.__defaultKombiConfigBaseDirectory()

            if self.group():
                configDirectory = configDirectory.joinpath(self.group())

            os.makedirs(configDirectory, exist_ok=True)
            self.__filePath = configDirectory / f'{self.name()}.json'

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

    def serialize(self):
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
            applicationData = pathlib.Path(os.path.expandvars('%APPDATA%'))
        elif os.name == 'posix':
            applicationData = home / '.local/share'
        elif sys.platform == 'darwin':
            applicationData = home / 'Library/Application Support'

        assert applicationData

        return applicationData / 'kombi'
