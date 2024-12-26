import xml.etree.ElementTree as ElementTree
from .AsciiElement import AsciiElement

class XmlElement(AsciiElement):
    """
    Xml element.
    """

    def __init__(self, *args, **kwargs):
        """
        Constructor.
        """
        super(XmlElement, self).__init__(*args, **kwargs)

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
    def test(cls, path, parentElement, ignoreExt=False):
        """
        Test if the path contains a xml file.
        """
        if not super(XmlElement, cls).test(path, parentElement):
            return False

        return ignoreExt or path.suffix[1:] == 'xml'

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
XmlElement.register(
    'xml',
    XmlElement
)
