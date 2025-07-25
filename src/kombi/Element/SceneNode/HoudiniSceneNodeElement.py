from ..Element import Element
from .SceneNodeElement import SceneNodeElement

try:
    import hou
except ImportError:
    houdiniAvailable = False
else:
    houdiniAvailable = True

class HoudiniSceneNodeElement(SceneNodeElement):
    """
    Implementation for a houdini scene node element.
    """

    def __init__(self, houNode, *args, **kwargs):
        """
        Create a HoudiniSceneNodeElement object.
        """
        super().__init__(houNode.path(), *args, **kwargs)
        self.setVar('fullPath', self.var('name'))
        self.setVar('nodeType', houNode.type().name())

        self.__node = houNode

    def node(self):
        """
        Return the hou node object.
        """
        return self.__node

    def select(self, groupedElements=None):
        """
        Select nodes in houdini.
        """
        elements = [self]
        if groupedElements:
            elements = groupedElements

        hou.clearAllSelected()
        for element in elements:
            element.node().setSelected(True)

    def serializeInitializationData(self):
        """
        Define the data passed during the initialization of the element.
        """
        return self.node().path()

    @classmethod
    def createFromName(cls, path):
        """
        Create a node element based on the path.
        """
        return Element.create(cls.parseInitializationData(path))

    @classmethod
    def parseInitializationData(cls, data):
        """
        Parse the serialized initialization data.
        """
        return hou.node(data)

    @classmethod
    def test(cls, houNode, _):
        """
        Test if the input contains a houdini node object.
        """
        if not houdiniAvailable:
            return False

        return isinstance(houNode, hou.Node)


# registration
Element.register(
    'houdiniSceneNode',
    HoudiniSceneNodeElement
)
