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

    # use the environment variable KOMBI_FSELEMENT_CACHE_SIZE to control
    # the number of path elements cached for faster file system queries over
    # the network. To disable caching, set KOMBI_FSELEMENT_CACHE_SIZE to 0.
    __pathCacheSize = int(os.environ.get('KOMBI_FSELEMENT_CACHE_SIZE', '50'))

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
        if 'sourceDirectory' not in self.varNames():
            if not path.is_dir():
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
        superclass, which can be expensive over the network. If the cache exceeds
        the maximum size, the oldest cached entry is removed.
        """
        # Using a combination of id(path) and hash(path) to ensure a unique identifier.
        # The object ID (from id()) can be repurposed by the garbage collector if the object is collected,
        # so combining it with hash(path) provides a more reliable way to uniquely identify the object
        # throughout its lifetime.
        pathId = (id(path), hash(path))

        # remove the oldest item when the cache exceeds the maximum size
        if len(FsElement.__pathCache) > FsElement.__pathCacheSize:
            FsElement.__pathCache.pop(next(iter(FsElement.__pathCache)))

        if pathId not in FsElement.__pathCache:
            FsElement.__pathCache[pathId] = {}

        if attr not in FsElement.__pathCache[pathId]:
            value = getattr(path, attr)
            if callable(value):
                value = value(*args, **kwargs)
            FsElement.__pathCache[pathId][attr] = value

        return FsElement.__pathCache[pathId][attr]

    @staticmethod
    def clearCache():
        """
        Clear the cached path query.
        """
        FsElement.__pathCache = {}

    def __setPath(self, path):
        """
        Set the path to the element.
        """
        assert isinstance(path, Path), \
            "Invalid Path type"

        self.__path = path
