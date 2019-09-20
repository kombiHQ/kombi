import os
import json
import traceback
from collections import OrderedDict
from .VarExtractor import VarExtractor

# compatibility with python 2/3
try:
    basestring
except NameError:
    basestring = str

class CrawlerError(Exception):
    """Crawler Error."""

class CrawlerInvalidVarError(CrawlerError):
    """Crawler Invalid Var Error."""

class CrawlerInvalidTagError(CrawlerError):
    """Invalid Tag Error."""

class CrawlerTestError(CrawlerError):
    """Crawler Test error."""

class CrawlerTypeError(CrawlerError):
    """Crawler Type Error."""

class Crawler(object):
    """
    Abstracted Crawler.
    """

    __registeredTypes = OrderedDict()

    def __init__(self, name, parentCrawler=None):
        """
        Create a crawler.
        """
        self.__vars = {}
        self.__tags = {}
        self.__contextVarNames = set()

        # passing variables
        if parentCrawler:
            assert isinstance(parentCrawler, Crawler), \
                "Invalid crawler type!"

            for varName in parentCrawler.varNames():
                isContextVar = (varName in parentCrawler.contextVarNames())
                self.setVar(varName, parentCrawler.var(varName), isContextVar)

            self.setVar(
                'fullPath',
                os.path.join(
                    parentCrawler.var('fullPath'),
                    name
                )
            )
        else:
            self.setVar('fullPath', '/')

        self.setVar('name', name)
        self.__globCache = None

    def isLeaf(self):
        """
        For re-implementation: Return a boolean telling if the crawler is leaf.
        """
        return True

    def children(self):
        """
        Return a list of crawlers.
        """
        assert not self.isLeaf(), "Can't compute children from a leaf crawler!"

        result = self._computeChildren()
        for crawler in result:
            assert isinstance(crawler, Crawler), \
                "Invalid Crawler Type"

        return result

    def varNames(self):
        """
        Return a list of variable names assigned to the crawler.
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
            raise CrawlerInvalidVarError(
                'Variable not found "{0}"'.format(name)
            )

        return self.__vars[name]

    def tagNames(self):
        """
        Return a list of tag names assigned to the crawler.
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
            raise CrawlerInvalidTagError(
                'Tag not found "{0}"'.format(name)
            )

        return self.__tags[name]

    def clone(self):
        """
        Return a cloned instance about the current crawler.
        """
        return Crawler.createFromJson(self.toJson())

    def toJson(self):
        """
        Serialize the crawler to json (it can be recovered later using fromJson).
        """
        crawlerContents = {
            "vars": {},
            "contextVarNames": [],
            "tags": {}
        }

        for varName in self.varNames():
            crawlerContents['vars'][varName] = self.var(varName)

        for varName in self.contextVarNames():
            crawlerContents['contextVarNames'].append(varName)

        for tagName in self.tagNames():
            crawlerContents['tags'][tagName] = self.tag(tagName)

        return json.dumps(
            crawlerContents,
            indent=4,
            separators=(',', ': ')
        )

    def glob(self, filterTypes=[], useCache=True):
        """
        Return a list of all crawlers found recursively under this path.

        Filter result list by crawler type (str) or class type (both include derived classes).
        """
        if self.__globCache is None or not useCache:
            # Recursively collect all crawlers for this path
            self.__globCache = Crawler.__collectCrawlers(self)

        if not filterTypes:
            return self.__globCache

        filteredCrawlers = set()
        for filterType in filterTypes:
            subClasses = tuple(Crawler.registeredSubclasses(filterType))
            filteredCrawlers.update(
                filter(lambda x: isinstance(x, subClasses), self.__globCache)
            )
        return list(filteredCrawlers)

    def __repr__(self):
        """
        Return a string representation for the crawler.
        """
        return "{}({})".format(
            self.__class__.__name__ if 'type' not in self.varNames() else self.var('type'),
            self.var('fullPath')
        )

    @classmethod
    def test(cls, data, parentCrawler=None):
        """
        Tells if crawler implementation, can handle it.

        For re-implementation: Should return a boolean telling if the
        crawler implementation can crawl the data.
        """
        raise NotImplementedError

    @staticmethod
    def create(data, parentCrawler=None):
        """
        Create a crawler for the input data.
        """
        result = None
        for registeredName in reversed(Crawler.__registeredTypes.keys()):
            crawlerTypeClass = Crawler.__registeredTypes[registeredName]
            passedTest = False

            # testing crawler
            try:
                passedTest = crawlerTypeClass.test(data, parentCrawler)
            except Exception as err:
                traceback.print_exc()

                raise CrawlerTestError(
                    'Error on testing a crawler "{}" for "{}"\n{}'.format(
                        registeredName,
                        data,
                        str(err)
                    )
                )

            # creating crawler
            if passedTest:
                try:
                    result = crawlerTypeClass(data, parentCrawler)
                except Exception as err:
                    traceback.print_exc()

                    raise CrawlerTypeError(
                        'Error on creating a crawler "{}" for "{}"\n{}'.format(
                            registeredName,
                            data,
                            str(err)
                        )
                    )
                else:
                    result.setVar('type', registeredName)
                break

        assert isinstance(result, Crawler),\
            "Don't know how to create a crawler for \"{0}\"".format(data)

        return result

    @staticmethod
    def register(name, crawlerClass):
        """
        Register a crawler type.

        The registration is used to tell the order that the crawler types
        are going to be tested. The test is done from the latest registrations to
        the first registrations (bottom top). The only exception is for types that
        get overridden where the position is going to be the same.
        """
        assert issubclass(crawlerClass, Crawler), \
            "Invalid crawler class!"

        Crawler.__registeredTypes[name] = crawlerClass

    @staticmethod
    def registeredType(name):
        """
        Return the crawler class registered with the given name.
        """
        assert name in Crawler.registeredNames(), "No registered crawler type for \"{0}\"".format(name)
        return Crawler.__registeredTypes[name]

    @staticmethod
    def registeredNames():
        """
        Return a list of registered crawler types.
        """
        return Crawler.__registeredTypes.keys()

    @staticmethod
    def registeredSubclasses(baseClassOrTypeName):
        """
        Return a list of registered subClasses for the given class or class type name.
        """
        baseClass = Crawler.__baseClass(baseClassOrTypeName)
        result = set()
        for registeredType in Crawler.__registeredTypes.values():
            if issubclass(registeredType, baseClass):
                result.add(registeredType)
        return list(result)

    @staticmethod
    def registeredSubTypes(baseClassOrTypeName):
        """
        Return a list of registered names of all derived classes for the given class or class type name.
        """
        baseClass = Crawler.__baseClass(baseClassOrTypeName)
        result = set()
        for name, registeredType in Crawler.__registeredTypes.items():
            if issubclass(registeredType, baseClass):
                result.add(name)
        return list(result)

    @staticmethod
    def createFromJson(jsonContents):
        """
        Create a crawler based on the jsonContents (serialized via toJson).
        """
        contents = json.loads(jsonContents)
        crawlerType = contents["vars"]["type"]
        fullPath = contents["vars"]["fullPath"]

        # creating crawler
        crawler = Crawler.__registeredTypes[crawlerType](fullPath)

        # setting vars
        for varName, varValue in contents["vars"].items():
            isContextVar = (varName in contents["contextVarNames"])
            crawler.setVar(varName, varValue, isContextVar)

        # setting tags
        for tagName, tagValue in contents["tags"].items():
            crawler.setTag(tagName, tagValue)

        return crawler

    @staticmethod
    def group(crawlers, tag='group'):
        """
        Return the crawlers grouped by the input tag.

        The result is a 2D array where each group of the result is a list of crawlers
        that contain the same tag value. The crawlers inside of the group are
        sorted alphabetically using the path by default. If you want to do a custom
        sorting, take a look at: Crawler.sortGroup
        """
        groupedCrawlers = OrderedDict()
        uniqueCrawlers = []
        for crawler in crawlers:
            if tag in crawler.tagNames():
                groupName = crawler.tag(tag)
                if groupName not in groupedCrawlers:
                    groupedCrawlers[groupName] = []
                groupedCrawlers[groupName].append(crawler)
            else:
                uniqueCrawlers.append([crawler])

        # sorting crawlers
        groupedSorted = Crawler.sortGroup(
            groupedCrawlers.values(),
            key=lambda x: x.var('fullPath')
        )

        return groupedSorted + uniqueCrawlers

    @staticmethod
    def sortGroup(crawlers, key=None, reverse=False):
        """
        Return a list of grouped crawlers sorted by the input key.
        """
        result = []
        for group in crawlers:
            result.append(list(sorted(group, key=key, reverse=reverse)))
        return result

    @staticmethod
    def __collectCrawlers(crawler):
        """
        Recursively collect crawlers.
        """
        result = []
        result.append(crawler)

        if not crawler.isLeaf():
            for childCrawler in crawler.children():
                result += Crawler.__collectCrawlers(childCrawler)

        return result

    @staticmethod
    def __baseClass(baseClassOrTypeName):
        """
        Return a valid base class for the given class or class type name.
        """
        if isinstance(baseClassOrTypeName, basestring):
            if baseClassOrTypeName not in Crawler.__registeredTypes:
                raise CrawlerTypeError(
                    'Crawler name is not a registered type: {}'.format(baseClassOrTypeName)
                )

            baseClass = Crawler.__registeredTypes[baseClassOrTypeName]
        else:
            assert issubclass(baseClassOrTypeName, Crawler)
            baseClass = baseClassOrTypeName
        return baseClass
