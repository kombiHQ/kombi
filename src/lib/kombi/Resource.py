import os
import sys
import traceback
from glob import glob
from collections import OrderedDict
from .KombiError import KombiError

class ResourceError(KombiError):
    """Resource error."""

class ResourceInvalidError(ResourceError):
    """Resource invalid Error."""

class Resource(object):
    """
    Class used to load custom resources to kombi.

    The resources can be custom elements, tasks, task wrappers (etc). By default
    any resource specified under the 'KOMBI_RESOURCE_PATH' is
    automatically loaded during the startup.

    The resources are simply python files that should import all the non-default
    modules under the _perform implementation.

    Also, make sure you always query the singleton instance through the "get"
    method.
    """

    __singleton = None
    __resourceEnvName = "KOMBI_RESOURCE_PATH"
    __resourceRaiseOnFailEnvName = "KOMBI_RESOURCE_RAISE_ON_FAIL"

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

        Used to load custom elements, template procedures, task wrappers...
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

    @classmethod
    def asciiBanner(cls, includeInfo=True):
        """
        Return the kombi ascii banner.
        """
        # This ASCII art is based on the original design found at
        # (credit to the creator, you rock!):
        # https://ascii.co.uk/art/vw
        asciiArt = [
            "  .---------------------------",
            "/--| |--| |--|  |-- \\----\\----\\",
            "|__| |__| |__|  |___ \\____\\____\\",
            "|=====================----------\\",
            "| === []   ._    ._   o\\      /o|",
            "|  __           __    ()\\    /()|",
            "| /  \\         /  \\      \\  /   |",
            "[] ( |--------| ( |_[==0======0==]",
            "  \\_/_/ \\_/_/  \\_/_/     \\_/_/"
        ]

        if includeInfo:
            asciiArt[4] += '  Kombi'
            asciiArt[5] += '  https://github.com/kombiHQ/kombi'

        return '\n'.join(asciiArt)

    def __loadToRuntime(self, filePath, source):
        """
        Execute a python resource.
        """
        try:
            with open(filePath) as f:
                code = compile(f.read(), filePath, 'exec')

                # we are going to provide a custom
                # globals for each resource during
                # the execution. This is necessary
                # to make sure that when we call __file__
                # it will return the resource full
                # path (rather than the current file)
                resGlobals = dict(globals())
                resGlobals['__file__'] = filePath

                exec(code, resGlobals)
        except Exception as err:
            sys.stderr.write(
                'Kombi error on loading resource: {}\n'.format(
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

                # skipping init files, as they likely contain relative imports,
                # which are not supported
                if os.path.basename(pythonFile).lower() == '__init__.py':
                    continue

                try:
                    self.__loadToRuntime(pythonFile, 'environment')
                except Exception as err:

                    if raiseOnResourceFail:
                        raise err

                    # printing the stacktrace
                    traceback.print_exc()
