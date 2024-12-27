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
        super().__init__(*args, **kwargs)
        self.setVar('name', pymelObject.name())

        self.__node = pymelObject

    def node(self):
        """
        Return the pymel object.
        """
        return self.__node

    def select(self):
        """
        Select the node.
        """
        raise self.node().select()

    def serializeInitializationData(self):
        """
        Define the data passed during the initialization of the element.
        """
        return self.node().name()

    @classmethod
    def parseInitializationData(cls, data):
        """
        Parse the serialized initialization data.
        """
        return pm.PyNode(data)

    @classmethod
    def test(cls, pymelObject, parentElement):
        """
        Test if the input contains a pymel object.
        """
        if not pymelAvailable or not super(SceneNodeElement, cls).test(pymelObject, parentElement):
            return False

        return isinstance(pymelObject, pm.PyNode)


# registration
Element.register(
    'mayaSceneNode',
    MayaSceneNodeElement
)
