from ..Element import Element
from .SceneNodeElement import SceneNodeElement

try:
    import pymel.core as pm
except ImportError:
    pymelAvailable = False
else:
    pymelAvailable = True

class MayaSceneNodeElement(SceneNodeElement):
    """
    Implementation for a maya scene node element using pymel.
    """

    def __init__(self, pymelObject, *args, **kwargs):
        """
        Create a MayaSceneNodeElement object.
        """
        super().__init__(pymelObject.name(long=True), *args, **kwargs)
        self.setVar('fullPath', self.var('name'))
        self.setVar('nodeType', pymelObject.type())

        self.__node = pymelObject

    def node(self):
        """
        Return the pymel object.
        """
        return self.__node

    def select(self, groupedElements=None):
        """
        Select in maya.
        """
        elements = [self]
        if groupedElements:
            elements = groupedElements

        # in case of a reference node, select all nodes from the reference instead
        # of the reference node itself
        nodes = []
        for element in elements:
            if element.node().type() == 'reference':
                nodes.extend(pm.referenceQuery(element.node(), nodes=True))
            else:
                nodes.append(element.node())

        pm.select(nodes)

    def filePath(self):
        """
        Return the file path associated with the asset.
        """
        if self.node().type() == 'reference':
            return pm.referenceQuery(self.node(), filename=True)
        return ''

    def serializeInitializationData(self):
        """
        Define the data passed during the initialization of the element.
        """
        return self.node().name(long=True)

    @classmethod
    def createFromName(cls, name):
        """
        Create a node element based on the name.
        """
        return Element.create(cls.parseInitializationData(name))

    @classmethod
    def parseInitializationData(cls, data):
        """
        Parse the serialized initialization data.
        """
        return pm.PyNode(data)

    @classmethod
    def test(cls, pymelObject, _):
        """
        Test if the input contains a pymel object.
        """
        if not pymelAvailable:
            return False

        return isinstance(pymelObject, pm.PyNode)


# registration
Element.register(
    'mayaSceneNode',
    MayaSceneNodeElement
)
