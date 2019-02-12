import os
import sys
import traceback
from glob import glob
from collections import OrderedDict

class ResourceError(Exception):
    """Resource error."""

class ResourceInvalidError(ResourceError):
    """Resource invalid Error."""

class Resource(object):
    """
    Class used to load custom resources to chilopoda.

    The resources can be custom crawlers, tasks, task wrappers (etc). By default
    any resource specified under the 'CHILOPODA_RESOURCE_PATH' is
    automatically loaded during the startup.

    The resources are simply python files that should import all the non-default
    modules under the _perform implementation.

    Also, make sure you always query the singleton instance through the "get"
    method.
    """

    __singleton = None
    __resourceEnvName = "CHILOPODA_RESOURCE_PATH"
    __resourceRaiseOnFailEnvName = "CHILOPODA_RESOURCE_RAISE_ON_FAIL"

    def __init__(self):
        """
        Create a resource class (@See Resource.get).
        """
        assert self.__singleton is None, "Can only have one instance!"

        self.__loadedPaths = OrderedDict()
        self.__loadResourceEnvPath()

    def load(self, filePath):
        """
        Load a python resource file to the runtime.

        Used to load custom crawlers, template procedures, task wrappers...
        """
        if not os.path.exists(filePath):
            raise ResourceInvalidError(
                'Invalid resource "{0}"!'.format(filePath)
            )

        self.__loadToRuntime(filePath, "external")

    def loaded(self, ignoreFromEnvironment=False):
        """
        Return a list of file paths that have been loaded as resource.
        """
        result = []
        for resourceFilePath, resourceSource in self.__loadedPaths.items():
            if not ignoreFromEnvironment or resourceSource != 'environment':
                result.append(resourceFilePath)

        return result

    @classmethod
    def get(cls):
        """
        Return the singleton resource instance.
        """
        if cls.__singleton is None:
            cls.__singleton = Resource()

        return cls.__singleton

    def __loadToRuntime(self, filePath, source):
        """
        Execute a python resource.
        """
        try:
            with open(filePath) as f:
                code = compile(f.read(), filePath, 'exec')
                exec(code, globals())
        except Exception as err:
            sys.stderr.write(
                'Chilopoda error on loading resource: {}\n'.format(
                    filePath
                )
            )
            raise err

        else:
            # removing any previous occurrence of the same file
            # we don't want to show duplicated resources
            if filePath in self.__loadedPaths:
                del self.__loadedPaths[filePath]

            self.__loadedPaths[filePath] = source

    def __loadResourceEnvPath(self):
        """
        Load all the resources under the resource path environment.
        """
        resourcePaths = os.environ.get(self.__resourceEnvName, '').split(os.pathsep)[::-1]

        # loading any python file under the resources path
        raiseOnResourceFail = os.environ.get(self.__resourceRaiseOnFailEnvName, '').lower() in ['1', 'true']
        for resourcePath in filter(os.path.exists, resourcePaths):
            for pythonFile in glob(os.path.join(resourcePath, '*.py')):
                try:
                    self.__loadToRuntime(pythonFile, 'environment')
                except Exception as err:

                    if raiseOnResourceFail:
                        raise err

                    # printing the stacktrace
                    traceback.print_exc()


# loading resources by triggering the singleton
Resource.get()
