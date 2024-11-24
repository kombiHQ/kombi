import os
import json
import traceback
from collections import OrderedDict
from .VarExtractor import VarExtractor

class InfoCrateError(Exception):
    """InfoCrate Error."""

class InfoCrateInvalidVarError(InfoCrateError):
    """InfoCrate Invalid Var Error."""

class InfoCrateInvalidTagError(InfoCrateError):
    """Invalid Tag Error."""

class InfoCrateTestError(InfoCrateError):
    """InfoCrate Test error."""

class InfoCrateTypeError(InfoCrateError):
    """InfoCrate Type Error."""

class InfoCrateContext(object):
    """
    InfoCrate context manager.

    # caching children (enabled by default)
    with InfoCrateContext():
        # querying children for the first time.
        for childInfoCrate in infoCrate.children():
            print(childInfoCrate, id(childInfoCrate))

        # since it's inside of the context manager
        # it will result the same children when
        # querying the children again.
        for childInfoCrate in infoCrate.children():
            print(childInfoCrate, id(childInfoCrate))
    """

    totalActiveScopes = 0

    def __init__(self, cacheChildren=True):
        """
        Create a infoCrate context object.
        """
        self.__enableCacheChildren = cacheChildren

    def __enter__(self):
        """
        Inside of the `with` statement we assigning a new cache.
        """
        if self.__enableCacheChildren:
            InfoCrateContext.totalActiveScopes += 1

    def __exit__(self, *args, **kwargs):
        """
        Restoring the previous cache value.
        """
        if self.__enableCacheChildren:
            InfoCrateContext.totalActiveScopes -= 1

    @classmethod
    def isChachingChildren(cls):
        """
        Return a boolean telling if the children is being cached.
        """
        return InfoCrateContext.totalActiveScopes > 0

class InfoCrate(object):
    """
    Abstracted InfoCrate.
    """

    __registeredTypes = OrderedDict()

    def __init__(self, name, parentInfoCrate=None):
        """
        Create a infoCrate.
        """
        self.__vars = {}
        self.__tags = {}
        self.__contextVarNames = set()
        self.__childrenCache = None

        # passing variables
        if parentInfoCrate:
            assert isinstance(parentInfoCrate, InfoCrate), \
                "Invalid infoCrate type!"

            for varName in parentInfoCrate.varNames():
                isContextVar = (varName in parentInfoCrate.contextVarNames())
                self.setVar(varName, parentInfoCrate.var(varName), isContextVar)

            self.setVar(
                'fullPath',
                os.path.join(
                    parentInfoCrate.var('fullPath'),
                    name
                )
            )
        else:
            self.setVar('fullPath', '/')

        self.setVar('name', name)
        self.__globCache = {}

    def isLeaf(self):
        """
        For re-implementation: Return a boolean telling if the infoCrate is leaf.
        """
        return True

    def setChildren(self, children):
        """
        Set a list of children infoCrates (trigged during loadFromJson).

        When querying children infoCrates make to sure to use InfoCrateContext. Otherwise,
        the children will be recomputed again.
        """
        assert not self.isLeaf(), "Can't set children in a leaf infoCrate!"
        assert isinstance(children, (list, tuple)), "Invalid infoCrate children list!"

        for infoCrate in children:
            assert isinstance(infoCrate, InfoCrate), \
                "Invalid InfoCrate Type"

        self.__childrenCache = list(children)

    def children(self):
        """
        Return a list of infoCrates.
        """
        assert not self.isLeaf(), "Can't compute children from a leaf infoCrate!"

        # returning form cache
        if InfoCrateContext.isChachingChildren() and self.__childrenCache is not None:
            return self.__childrenCache

        # computing children
        result = self._computeChildren()
        for infoCrate in result:
            assert isinstance(infoCrate, InfoCrate), \
                "Invalid InfoCrate Type"

        # assigning the cache
        if InfoCrateContext.isChachingChildren():
            self.__childrenCache = result
        # invalidating any existing cache
        else:
            self.__childrenCache = None

        return result

    def flushChildrenCache(self):
        """
        Flushes the cache for the children.

        The cache is only enabled when using the context manager InfoCrateContext.
        """
        self.__childrenCache = None

    def varNames(self):
        """
        Return a list of variable names assigned to the infoCrate.
        """
        return list(self.__vars.keys())

    def contextVarNames(self):
        """
        Return a list of variable names that are defined as context variables.
        """
        return list(self.__contextVarNames)

    def assignVars(self, varExtractor):
        """
        Assign variables from a var extractor instance.
        """
        assert isinstance(varExtractor, VarExtractor), "Invalid VarExtractor type!"
        assert varExtractor.match(), "varExtractor failed during the extraction!"

        contextVarNames = varExtractor.contextVarNames()
        for varName in varExtractor.varNames():
            self.setVar(
                varName,
                varExtractor.var(varName),
                isContextVar=(varName in contextVarNames)
            )

    def setVar(self, name, value, isContextVar=False):
        """
        Set a value for a variable.
        """
        if isContextVar:
            self.__contextVarNames.add(name)
        elif name in self.__contextVarNames:
            self.__contextVarNames.remove(name)

        self.__vars[name] = value

    def var(self, name):
        """
        Return the value for a variable.
        """
        if name not in self.__vars:
            raise InfoCrateInvalidVarError(
                'Variable not found "{0}"'.format(name)
            )

        return self.__vars[name]

    def tagNames(self):
        """
        Return a list of tag names assigned to the infoCrate.
        """
        return self.__tags.keys()

    def setTag(self, name, value):
        """
        Set a value for a tag.
        """
        self.__tags[name] = value

    def tag(self, name):
        """
        Return the value for a tag.
        """
        if name not in self.__tags:
            raise InfoCrateInvalidTagError(
                'Tag not found "{0}"'.format(name)
            )

        return self.__tags[name]

    def clone(self):
        """
        Return a cloned instance about the current infoCrate.
        """
        return InfoCrate.createFromJson(self.toJson())

    def toJson(self):
        """
        Serialize the infoCrate to json (it can be recovered later using fromJson).
        """
        infoCrateContents = {
            "vars": {},
            "contextVarNames": [],
            "tags": {},
            "children": None,
            "initializationData": self.initializationData()
        }

        # serializing the children as well when caching is enabled
        if not self.isLeaf() and self.__childrenCache is not None:
            infoCrateContents['children'] = []
            for child in self.__childrenCache:
                infoCrateContents['children'].append(child.toJson())

        for varName in self.varNames():
            infoCrateContents['vars'][varName] = self.var(varName)

        assert 'type' in infoCrateContents['vars'], \
            "Missing type var, cannot serialize infoCrate (perhaps it was not created through InfoCrate.create)."

        for varName in self.contextVarNames():
            infoCrateContents['contextVarNames'].append(varName)

        for tagName in self.tagNames():
            infoCrateContents['tags'][tagName] = self.tag(tagName)

        return json.dumps(
            infoCrateContents,
            indent=4,
            separators=(',', ': ')
        )

    def initializationData(self):
        """
        Define the data passed during the initialization of the infoCrate.
        """
        return self.var('fullPath')

    def glob(self, filterTypes=[], recursive=True, useCache=True):
        """
        Return a list of all infoCrates under this path.

        Filter result list by infoCrate type (str) or class type (both include derived classes).
        """
        cacheKey = (recursive,)
        if cacheKey not in self.__globCache or not useCache:
            self.__globCache[cacheKey] = InfoCrate.__collectInfoCrates(self, recursive)

        if not filterTypes:
            return self.__globCache[cacheKey]

        filteredInfoCrates = set()
        for filterType in filterTypes:
            subClasses = tuple(InfoCrate.registeredSubclasses(filterType))
            filteredInfoCrates.update(
                filter(lambda x: isinstance(x, subClasses), self.__globCache[cacheKey])
            )
        return list(filteredInfoCrates)

    def __repr__(self):
        """
        Return a string representation for the infoCrate.
        """
        return "{}({})".format(
            self.__class__.__name__ if 'type' not in self.varNames() else self.var('type'),
            self.var('fullPath')
        )

    @classmethod
    def test(cls, data, parentInfoCrate=None):
        """
        Tells if infoCrate implementation, can handle it.

        For re-implementation: Should return a boolean telling if the
        infoCrate implementation can crawl the data.
        """
        raise NotImplementedError

    @staticmethod
    def create(data, parentInfoCrate=None):
        """
        Create a infoCrate for the input data.
        """
        result = None
        for registeredName in reversed(InfoCrate.__registeredTypes.keys()):
            infoCrateTypeClass = InfoCrate.__registeredTypes[registeredName]
            passedTest = False

            # testing infoCrate
            try:
                passedTest = infoCrateTypeClass.test(data, parentInfoCrate)
            except Exception as err:
                traceback.print_exc()

                raise InfoCrateTestError(
                    'Error on testing a infoCrate "{}" for "{}"\n{}'.format(
                        registeredName,
                        data,
                        str(err)
                    )
                )

            # creating infoCrate
            if passedTest:
                try:
                    result = infoCrateTypeClass(data, parentInfoCrate)
                except Exception as err:
                    traceback.print_exc()

                    raise InfoCrateTypeError(
                        'Error on creating a infoCrate "{}" for "{}"\n{}'.format(
                            registeredName,
                            data,
                            str(err)
                        )
                    )
                else:
                    result.setVar('type', registeredName)
                break

        assert isinstance(result, InfoCrate), \
            "Don't know how to create a infoCrate for \"{0}\"".format(data)

        return result

    @staticmethod
    def register(name, infoCrateClass, overrideAsLatest=False):
        """
        Register a infoCrate type.

        The registration is used to tell the order that the infoCrate types
        are going to be tested. The test is done from the latest registrations to
        the first registrations (bottom top). The only exception is for types that
        get overridden where the position is going to be the same (when
        overrideAsLatest is set to false).
        """
        assert issubclass(infoCrateClass, InfoCrate), \
            "Invalid infoCrate class!"

        if overrideAsLatest and name in InfoCrate.__registeredTypes:
            del InfoCrate.__registeredTypes[name]

        InfoCrate.__registeredTypes[name] = infoCrateClass

    @staticmethod
    def registeredType(name):
        """
        Return the infoCrate class registered with the given name.
        """
        assert name in InfoCrate.registeredNames(), "No registered infoCrate type for \"{0}\"".format(name)
        return InfoCrate.__registeredTypes[name]

    @staticmethod
    def registeredNames():
        """
        Return a list of registered infoCrate types.
        """
        return InfoCrate.__registeredTypes.keys()

    @staticmethod
    def registeredSubclasses(baseClassOrTypeName):
        """
        Return a list of registered subClasses for the given class or class type name.
        """
        baseClass = InfoCrate.__baseClass(baseClassOrTypeName)
        result = set()
        for registeredType in InfoCrate.__registeredTypes.values():
            if issubclass(registeredType, baseClass):
                result.add(registeredType)
        return list(result)

    @staticmethod
    def registeredSubTypes(baseClassOrTypeName):
        """
        Return a list of registered names of all derived classes for the given class or class type name.
        """
        baseClass = InfoCrate.__baseClass(baseClassOrTypeName)
        result = set()
        for name, registeredType in InfoCrate.__registeredTypes.items():
            if issubclass(registeredType, baseClass):
                result.add(name)
        return list(result)

    @staticmethod
    def createFromJson(jsonContents):
        """
        Create a infoCrate based on the jsonContents (serialized via toJson).
        """
        contents = json.loads(jsonContents)
        infoCrateType = contents["vars"]["type"]
        initializationData = contents['initializationData']

        # creating infoCrate
        infoCrate = InfoCrate.__registeredTypes[infoCrateType](initializationData)

        # loading baked children infoCrates
        if not infoCrate.isLeaf() and contents['children'] is not None:
            children = []
            for childBakedJsonInfoCrate in contents['children']:
                children.append(InfoCrate.createFromJson(childBakedJsonInfoCrate))

            infoCrate.setChildren(children)

        # setting vars
        for varName, varValue in contents["vars"].items():
            isContextVar = (varName in contents["contextVarNames"])
            infoCrate.setVar(varName, varValue, isContextVar)

        # setting tags
        for tagName, tagValue in contents["tags"].items():
            infoCrate.setTag(tagName, tagValue)

        return infoCrate

    @staticmethod
    def group(infoCrates, tag='group'):
        """
        Return the infoCrates grouped by the input tag.

        The result is a 2D array where each group of the result is a list of infoCrates
        that contain the same tag value. The infoCrates inside of the group are
        sorted alphabetically using the path by default. If you want to do a custom
        sorting, take a look at: InfoCrate.sortGroup
        """
        groupedInfoCrates = OrderedDict()
        uniqueInfoCrates = []
        for infoCrate in infoCrates:
            if tag in infoCrate.tagNames():
                groupName = infoCrate.tag(tag)
                if groupName not in groupedInfoCrates:
                    groupedInfoCrates[groupName] = []
                groupedInfoCrates[groupName].append(infoCrate)
            else:
                uniqueInfoCrates.append([infoCrate])

        # sorting infoCrates
        groupedSorted = InfoCrate.sortGroup(
            groupedInfoCrates.values(),
            key=lambda x: x.var('fullPath')
        )

        return groupedSorted + uniqueInfoCrates

    @staticmethod
    def sortGroup(infoCrates, key=None, reverse=False):
        """
        Return a list of grouped infoCrates sorted by the input key.
        """
        result = []
        for group in infoCrates:
            result.append(list(sorted(group, key=key, reverse=reverse)))
        return result

    @staticmethod
    def __collectInfoCrates(infoCrate, recursive):
        """
        Recursively collect infoCrates.
        """
        if infoCrate.isLeaf():
            return []

        result = []
        for childInfoCrate in infoCrate.children():
            result.append(childInfoCrate)
            if recursive:
                result += InfoCrate.__collectInfoCrates(childInfoCrate, True)

        return result

    @staticmethod
    def __baseClass(baseClassOrTypeName):
        """
        Return a valid base class for the given class or class type name.
        """
        if isinstance(baseClassOrTypeName, str):
            if baseClassOrTypeName not in InfoCrate.__registeredTypes:
                raise InfoCrateTypeError(
                    'InfoCrate name is not a registered type: {}'.format(baseClassOrTypeName)
                )

            baseClass = InfoCrate.__registeredTypes[baseClassOrTypeName]
        else:
            assert issubclass(baseClassOrTypeName, InfoCrate)
            baseClass = baseClassOrTypeName
        return baseClass
