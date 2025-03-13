import os
import sys
from pathlib import Path
from .. import Element

class FsElement(Element):
    """
    Abstracted file system Path.
    """
    __invalidPath = None
    __pathCache = {}

    # the path cache speeds up data retrieval over the network by storing previously fetched results.
    # However, it may cause data to become outdated. Therefore, use the environment KOMBI_FSELEMENT_ENABLE_CACHE
    # to disable caching if needed.
    __usePathCache = bool(os.environ.get('KOMBI_FSELEMENT_ENABLE_CACHE', '1').lower() in ('1', 'true'))
    __asciiCharacters = ''.join(
        [chr(code) for code in range(32, 127)] + list('\b\f\n\r\t')
    )

    def __init__(self, pathStrOrPath, parentElement=None):
        """
        Create a element (use the factory function Path.create instead).
        """
        if isinstance(pathStrOrPath, str):
            path = Path(pathStrOrPath)
        else:
            path = pathStrOrPath

        super(FsElement, self).__init__(path.name, parentElement)

        self.__setPath(path)
        self.setVar('filePath', str(path))
        self.setVar('fullPath', self.var('filePath'))
        self.setVar('ext', path.suffix[1:])
        self.setVar('baseName', path.name)
        self.setVar('name', self.var('baseName'))
        if 'sourceDirectory' not in self.varNames() and not self.cachedPathQuery(path, 'is_dir'):
            self.setVar('sourceDirectory', str(path.parent))

    def path(self):
        """
        Return the path object used to create the element.
        """
        return self.__path

    def globFromParent(self, filterTypes=[], useCache=True):
        """
        Return a list of all elements found recursively under the parent directory of the given path.

        Filter result list by exact element type (str) or class type (includes derived classes).
        """
        parentPath = os.path.dirname(self.var("filePath"))
        return FsElement.createFromPath(parentPath).glob(filterTypes, useCache)

    @classmethod
    def test(cls, data=None, parentElement=None):
        """
        Tests if the data is a Path from pathlib.
        """
        if isinstance(data, Path):
            if cls.cachedPathQuery(data, 'exists'):
                FsElement.__invalidPath = None
                return True
            # since this input will be tested against all derived classes,
            # we will print the message only once per input.
            elif FsElement.__invalidPath != data:
                FsElement.__invalidPath = data
                sys.stderr.write(f'FsElement does not exist (invalid path): {data}\n')
                sys.stderr.flush()
        return False

    @staticmethod
    def createFromPath(fullPath, elementType=None, parentElement=None):
        """
        Create a element directly from a path string.
        """
        if elementType:
            elementClass = FsElement.registeredType(elementType)
            assert elementClass, "Invalid element type {} for {}".format(elementType, fullPath)

            result = elementClass(Path(fullPath), parentElement)
            result.setVar('type', elementType)

            return result
        else:
            return FsElement.create(Path(fullPath), parentElement)

    @staticmethod
    def cachedPathQuery(path, attr, *args, **kwargs):
        """
        Retrieve or compute and cache the value of an attribute for the given path.

        The path query results are cached to improve performance, as the same path
        might be queried multiple times by different element types calling the
        superclass, which can be expensive over the network.
        """
        pathId = hash(path)

        if pathId not in FsElement.__pathCache:
            FsElement.__pathCache[pathId] = {}

        if not FsElement.__usePathCache or attr not in FsElement.__pathCache[pathId]:
            value = getattr(path, attr)
            if callable(value):
                value = value(*args, **kwargs)
            FsElement.__pathCache[pathId][attr] = value

        return FsElement.__pathCache[pathId][attr]
    
    @staticmethod
    def setCachedPathQuery(path, attr, value):
        """
        Set a computed value for a specified attribute in the cache.
        """
        pathId = hash(path)
        if pathId not in FsElement.__pathCache:
            FsElement.__pathCache[pathId] = {}
        FsElement.__pathCache[pathId][attr] = value

    @staticmethod
    def clearCache():
        """
        Clear the cached path query.
        """
        FsElement.__pathCache = {}

    @classmethod
    def isBinary(cls, filePath, readBytes=512, threshold=0.3):
        """
        Return a boolean telling if input file path is a binary file.

        Implementation based on:
        https://gist.github.com/magnetikonline/7a21ec5f5bcdbf7adb92f9d617e6198f
        """
        # read chunk of file
        with open(filePath, 'r', encoding='ISO-8859-1') as f:
            fileData = f.read(readBytes)

        # store chunk length read
        dataLength = len(fileData)
        if not dataLength:
            # empty files considered ascii
            return False

        if '\x00' in fileData:
            # file containing null bytes is binary
            return True

        # remove all text characters from file chunk, get remaining length
        binaryLength = len(list(filter(lambda x: x not in cls.__asciiCharacters, fileData)))

        # if percentage of binary characters above threshold, binary file
        return (float(binaryLength) / dataLength) >= threshold

    def __setPath(self, path):
        """
        Set the path to the element.
        """
        assert isinstance(path, Path), \
            "Invalid Path type"

        self.__path = path
