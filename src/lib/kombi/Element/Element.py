import os
import json
import traceback
from collections import OrderedDict
from .VarExtractor import VarExtractor

class ElementError(Exception):
    """Element Error."""

class ElementInvalidVarError(ElementError):
    """Element Invalid Var Error."""

class ElementInvalidTagError(ElementError):
    """Invalid Tag Error."""

class ElementTestError(ElementError):
    """Element Test error."""

class ElementTypeError(ElementError):
    """Element Type Error."""

class ElementContext(object):
    """
    Element context manager.

    # caching children (enabled by default)
    with ElementContext():
        # querying children for the first time.
        for childElement in element.children():
            print(childElement, id(childElement))

        # since it's inside of the context manager
        # it will result the same children when
        # querying the children again.
        for childElement in element.children():
            print(childElement, id(childElement))
    """

    totalActiveScopes = 0

    def __init__(self, cacheChildren=True):
        """
        Create a element context object.
        """
        self.__enableCacheChildren = cacheChildren

    def __enter__(self):
        """
        Inside of the `with` statement we assigning a new cache.
        """
        if self.__enableCacheChildren:
            ElementContext.totalActiveScopes += 1

    def __exit__(self, *args, **kwargs):
        """
        Restoring the previous cache value.
        """
        if self.__enableCacheChildren:
            ElementContext.totalActiveScopes -= 1

    @classmethod
    def isChachingChildren(cls):
        """
        Return a boolean telling if the children is being cached.
        """
        return ElementContext.totalActiveScopes > 0

class Element(object):
    """
    Abstracted Element.
    """

    __registeredTypes = OrderedDict()

    def __init__(self, name, parentElement=None):
        """
        Create a element.
        """
        self.__vars = {}
        self.__tags = {}
        self.__contextVarNames = set()
        self.__childrenCache = None

        # passing variables
        if parentElement:
            assert isinstance(parentElement, Element), \
                "Invalid element type!"

            for varName in parentElement.varNames():
                isContextVar = (varName in parentElement.contextVarNames())
                self.setVar(varName, parentElement.var(varName), isContextVar)

            self.setVar(
                'fullPath',
                os.path.join(
                    parentElement.var('fullPath'),
                    name
                )
            )
        else:
            self.setVar('fullPath', '/')

        self.setVar('name', name)
        self.__globCache = {}

    def isLeaf(self):
        """
        For re-implementation: Return a boolean telling if the element is leaf.
        """
        return True

    def setChildren(self, children):
        """
        Set a list of children elements (trigged during loadFromJson).

        When querying children elements make to sure to use ElementContext. Otherwise,
        the children will be recomputed again.
        """
        assert not self.isLeaf(), "Can't set children in a leaf element!"
        assert isinstance(children, (list, tuple)), "Invalid element children list!"

        for element in children:
            assert isinstance(element, Element), \
                "Invalid Element Type"

        self.__childrenCache = list(children)

    def children(self):
        """
        Return a list of elements.
        """
        assert not self.isLeaf(), "Can't compute children from a leaf element!"

        # returning form cache
        if ElementContext.isChachingChildren() and self.__childrenCache is not None:
            return self.__childrenCache

        # computing children
        result = self._computeChildren()
        for element in result:
            assert isinstance(element, Element), \
                "Invalid Element Type"

        # assigning the cache
        if ElementContext.isChachingChildren():
            self.__childrenCache = result
        # invalidating any existing cache
        else:
            self.__childrenCache = None

        return result

    def flushChildrenCache(self):
        """
        Flushes the cache for the children.

        The cache is only enabled when using the context manager ElementContext.
        """
        self.__childrenCache = None

    def varNames(self):
        """
        Return a list of variable names assigned to the element.
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
            raise ElementInvalidVarError(
                'Variable not found "{0}"'.format(name)
            )

        return self.__vars[name]

    def tagNames(self):
        """
        Return a list of tag names assigned to the element.
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
            raise ElementInvalidTagError(
                'Tag not found "{0}"'.format(name)
            )

        return self.__tags[name]

    def clone(self):
        """
        Return a cloned instance about the current element.
        """
        return Element.createFromJson(self.toJson())

    def toJson(self):
        """
        Serialize the element to json (it can be recovered later using fromJson).
        """
        elementContents = {
            "vars": {},
            "contextVarNames": [],
            "tags": {},
            "children": None,
            "initializationData": self.initializationData()
        }

        # serializing the children as well when caching is enabled
        if not self.isLeaf() and self.__childrenCache is not None:
            elementContents['children'] = []
            for child in self.__childrenCache:
                elementContents['children'].append(child.toJson())

        for varName in self.varNames():
            elementContents['vars'][varName] = self.var(varName)

        assert 'type' in elementContents['vars'], \
            "Missing type var, cannot serialize element (perhaps it was not created through Element.create)."

        for varName in self.contextVarNames():
            elementContents['contextVarNames'].append(varName)

        for tagName in self.tagNames():
            elementContents['tags'][tagName] = self.tag(tagName)

        return json.dumps(
            elementContents,
            indent=4,
            separators=(',', ': ')
        )

    def initializationData(self):
        """
        Define the data passed during the initialization of the element.
        """
        return self.var('fullPath')

    def glob(self, filterTypes=[], recursive=True, useCache=True):
        """
        Return a list of all elements under this path.

        Filter result list by element type (str) or class type (both include derived classes).
        """
        cacheKey = (recursive,)
        if cacheKey not in self.__globCache or not useCache:
            self.__globCache[cacheKey] = Element.__collectElements(self, recursive)

        if not filterTypes:
            return self.__globCache[cacheKey]

        filteredElements = set()
        for filterType in filterTypes:
            subClasses = tuple(Element.registeredSubclasses(filterType))
            filteredElements.update(
                filter(lambda x: isinstance(x, subClasses), self.__globCache[cacheKey])
            )
        return list(filteredElements)

    def __repr__(self):
        """
        Return a string representation for the element.
        """
        return "{}({})".format(
            self.__class__.__name__ if 'type' not in self.varNames() else self.var('type'),
            self.var('fullPath')
        )

    @classmethod
    def test(cls, data, parentElement=None):
        """
        Tells if element implementation, can handle it.

        For re-implementation: Should return a boolean telling if the
        element implementation can crawl the data.
        """
        raise NotImplementedError

    @staticmethod
    def create(data, parentElement=None):
        """
        Create a element for the input data.
        """
        result = None
        for registeredName in reversed(Element.__registeredTypes.keys()):
            elementTypeClass = Element.__registeredTypes[registeredName]
            passedTest = False

            # testing element
            try:
                passedTest = elementTypeClass.test(data, parentElement)
            except Exception as err:
                traceback.print_exc()

                raise ElementTestError(
                    'Error on testing a element "{}" for "{}"\n{}'.format(
                        registeredName,
                        data,
                        str(err)
                    )
                )

            # creating element
            if passedTest:
                try:
                    result = elementTypeClass(data, parentElement)
                except Exception as err:
                    traceback.print_exc()

                    raise ElementTypeError(
                        'Error on creating a element "{}" for "{}"\n{}'.format(
                            registeredName,
                            data,
                            str(err)
                        )
                    )
                else:
                    result.setVar('type', registeredName)
                break

        assert isinstance(result, Element), \
            "Don't know how to create a element for \"{0}\"".format(data)

        return result

    @staticmethod
    def register(name, elementClass, overrideAsLatest=False):
        """
        Register a element type.

        The registration is used to tell the order that the element types
        are going to be tested. The test is done from the latest registrations to
        the first registrations (bottom top). The only exception is for types that
        get overridden where the position is going to be the same (when
        overrideAsLatest is set to false).
        """
        assert issubclass(elementClass, Element), \
            "Invalid element class!"

        if overrideAsLatest and name in Element.__registeredTypes:
            del Element.__registeredTypes[name]

        Element.__registeredTypes[name] = elementClass

    @staticmethod
    def registeredType(name):
        """
        Return the element class registered with the given name.
        """
        assert name in Element.registeredNames(), "No registered element type for \"{0}\"".format(name)
        return Element.__registeredTypes[name]

    @staticmethod
    def registeredNames():
        """
        Return a list of registered element types.
        """
        return Element.__registeredTypes.keys()

    @staticmethod
    def registeredSubclasses(baseClassOrTypeName):
        """
        Return a list of registered subClasses for the given class or class type name.
        """
        baseClass = Element.__baseClass(baseClassOrTypeName)
        result = set()
        for registeredType in Element.__registeredTypes.values():
            if issubclass(registeredType, baseClass):
                result.add(registeredType)
        return list(result)

    @staticmethod
    def registeredSubTypes(baseClassOrTypeName):
        """
        Return a list of registered names of all derived classes for the given class or class type name.
        """
        baseClass = Element.__baseClass(baseClassOrTypeName)
        result = set()
        for name, registeredType in Element.__registeredTypes.items():
            if issubclass(registeredType, baseClass):
                result.add(name)
        return list(result)

    @staticmethod
    def createFromJson(jsonContents):
        """
        Create a element based on the jsonContents (serialized via toJson).
        """
        contents = json.loads(jsonContents)
        elementType = contents["vars"]["type"]
        initializationData = contents['initializationData']

        # creating element
        element = Element.__registeredTypes[elementType](initializationData)

        # loading baked children elements
        if not element.isLeaf() and contents['children'] is not None:
            children = []
            for childBakedJsonElement in contents['children']:
                children.append(Element.createFromJson(childBakedJsonElement))

            element.setChildren(children)

        # setting vars
        for varName, varValue in contents["vars"].items():
            isContextVar = (varName in contents["contextVarNames"])
            element.setVar(varName, varValue, isContextVar)

        # setting tags
        for tagName, tagValue in contents["tags"].items():
            element.setTag(tagName, tagValue)

        return element

    @staticmethod
    def group(elements, tag='group'):
        """
        Return the elements grouped by the input tag.

        The result is a 2D array where each group of the result is a list of elements
        that contain the same tag value. The elements inside of the group are
        sorted alphabetically using the path by default. If you want to do a custom
        sorting, take a look at: Element.sortGroup
        """
        groupedElements = OrderedDict()
        uniqueElements = []
        for element in elements:
            if tag in element.tagNames():
                groupName = element.tag(tag)
                if groupName not in groupedElements:
                    groupedElements[groupName] = []
                groupedElements[groupName].append(element)
            else:
                uniqueElements.append([element])

        # sorting elements
        groupedSorted = Element.sortGroup(
            groupedElements.values(),
            key=lambda x: x.var('fullPath')
        )

        return groupedSorted + uniqueElements

    @staticmethod
    def sortGroup(elements, key=None, reverse=False):
        """
        Return a list of grouped elements sorted by the input key.
        """
        result = []
        for group in elements:
            result.append(list(sorted(group, key=key, reverse=reverse)))
        return result

    @staticmethod
    def __collectElements(element, recursive):
        """
        Recursively collect elements.
        """
        if element.isLeaf():
            return []

        result = []
        for childElement in element.children():
            result.append(childElement)
            if recursive:
                result += Element.__collectElements(childElement, True)

        return result

    @staticmethod
    def __baseClass(baseClassOrTypeName):
        """
        Return a valid base class for the given class or class type name.
        """
        if isinstance(baseClassOrTypeName, str):
            if baseClassOrTypeName not in Element.__registeredTypes:
                raise ElementTypeError(
                    'Element name is not a registered type: {}'.format(baseClassOrTypeName)
                )

            baseClass = Element.__registeredTypes[baseClassOrTypeName]
        else:
            assert issubclass(baseClassOrTypeName, Element)
            baseClass = baseClassOrTypeName
        return baseClass
