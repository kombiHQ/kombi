from ..Element import Element

class CollectionElement(Element):
    """
    Collection element.
    """

    def __init__(self, elementList, parentElement=None):
        """
        Create a CollectionElement object.
        """
        super(CollectionElement, self).__init__('collection', parentElement)

        self.__children = list(elementList)

        # setting icon
        self.setTag('icon', 'icons/elements/children.png')

    def isLeaf(self):
        """
        Return a boolean telling if the element is leaf.
        """
        return False

    def serializeInitializationData(self):
        """
        Define the data passed during the initialization of the element.
        """
        return list(map(lambda x: x.toJson(), self.__children))

    @classmethod
    def parseInitializationData(cls, data):
        """
        Parse the serialized initialization data.
        """
        return list(map(lambda x: Element.createFromJson(x), data))

    @classmethod
    def test(cls, elementList, parentElement=None):
        """
        Test if it cotains a list of elements.
        """
        if not isinstance(elementList, (tuple, list)) or len(elementList) == 0:
            return False

        for element in elementList:
            if not isinstance(element, Element):
                return False

        return True

    def _computeChildren(self):
        """
        Return the collection contents.
        """
        return self.__children


Element.register(
    'collection',
    CollectionElement
)
