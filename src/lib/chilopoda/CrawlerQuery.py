from collections import OrderedDict
from .Template import Template
from .CrawlerMatcher import CrawlerMatcher

class CrawlerQuery(object):
    """
    Query the crawlers that meet the specification.
    """

    def __init__(self, crawlerMatcher, targetTemplate, filterTemplate):
        """
        Create a template resolver object.
        """
        self.__setCrawlerMatcher(crawlerMatcher)
        self.__setTargetTemplate(targetTemplate)
        self.__setFilterTemplate(filterTemplate)

    def crawlerMatcher(self):
        """
        Return the crawler path matcher that defines the specification.
        """
        return self.__crawlerMatcher

    def targetTemplate(self):
        """
        Return the target template.
        """
        return self.__targetTemplate

    def filterTemplate(self):
        """
        Return the filter template.
        """
        return self.__filterTemplate

    def query(self, crawlers, extraVars={}):
        """
        Return a dict containing the matched crawler as key and resolved template as value.
        """
        validCrawlers = {}
        for crawler in crawlers:
            if self.crawlerMatcher().match(crawler):
                filterTemplateValue = self.filterTemplate().valueFromCrawler(crawler, extraVars)

                # if the value of the filter is 0 or false the crawler is ignored
                if str(filterTemplateValue).lower() in ['false', '0']:
                    continue

                validCrawlers[crawler] = self.targetTemplate().valueFromCrawler(crawler, extraVars)

        # sorting result
        result = OrderedDict()
        for crawler, filePath in sorted(validCrawlers.items(), key=lambda x: (x[1], x[0].var('fullPath'))):
            result[crawler] = filePath

        return result

    def __setCrawlerMatcher(self, crawlerMatcher):
        """
        Set a crawler matcher.
        """
        assert isinstance(crawlerMatcher, CrawlerMatcher), \
            "Invalid crawler matcher type!"

        self.__crawlerMatcher = crawlerMatcher

    def __setTargetTemplate(self, template):
        """
        Set the target template.
        """
        assert isinstance(template, Template), \
            "Invalid template type!"

        self.__targetTemplate = template

    def __setFilterTemplate(self, template):
        """
        Set the target template.
        """
        assert isinstance(template, Template), \
            "Invalid template type!"

        self.__filterTemplate = template
