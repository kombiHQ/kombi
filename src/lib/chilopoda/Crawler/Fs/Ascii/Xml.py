import xml.etree.ElementTree as ElementTree
from ..Ascii import Ascii

class Xml(Ascii):
    """
    Xml crawler.
    """

    def __init__(self, *args, **kwargs):
        """
        Constructor.
        """
        super(Xml, self).__init__(*args, **kwargs)

        self.__cache = {}

    def queryTag(self, tag, ignoreNameSpace=True):
        """
        Query the values that are related to the specified tag.

        :param tag: The tag to search over the xml
        :type tag: str
        :param ignoreNameSpace: Flag to ignore the xml namespace
        :type ignoreNameSpace: boolean
        """
        return self.__runQueryTag(tag, ignoreNameSpace)

    @classmethod
    def test(cls, pathHolder, parentCrawler):
        """
        Test if the path holder contains a xml file.
        """
        return pathHolder.ext() == 'xml'

    def __runQueryTag(self, tag, ignoreNameSpace, root=None):
        """
        Run the recursion on the xml tree.

        :param tag: The tag to search over the xml
        :type tag: str
        :param ignoreNameSpace: Flag to ignore the xml namespace
        :type ignoreNameSpace: boolean
        :param root: A element tree from the xml
        :type root: xml.etree.ElementTree
        """
        firstCall = False

        if root is None:
            firstCall = True
            filePath = self.var('filePath')

            if filePath not in self.__cache:
                self.__cache[filePath] = ElementTree.parse(filePath).getroot()
            root = self.__cache[filePath]

        xmlTag = root.tag.split('}')[-1] if ignoreNameSpace else root.tag
        if tag == xmlTag:
            return (root.text, root.attrib)

        children = list(root)
        for child in children:
            result = self.__runQueryTag(tag, ignoreNameSpace, child)
            if result:
                return result

        if firstCall:
            raise ValueError('No tag with the name "{}" was found'.format(tag))


# registration
Xml.register(
    'xml',
    Xml
)
