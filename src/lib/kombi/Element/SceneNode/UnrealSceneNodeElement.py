from ..Element import Element
from .SceneNodeElement import SceneNodeElement

try:
    import unreal
except ImportError:
    unrealAvailable = False
else:
    unrealAvailable = True

class UnrealSceneNodeElement(SceneNodeElement):
    """
    Implementation for a unreal object element.
    """

    def __init__(self, assetData, *args, **kwargs):
        """
        Create a UnrealSceneNodeElement object.
        """
        super().__init__(*args, **kwargs)
        self.setVar('name', assetData.package_name)

        self.__node = assetData

    def node(self):
        """
        Return the unreal object.
        """
        return self.__node

    def select(self):
        """
        Select the node (disabled).
        """
        pass

    def serializeInitializationData(self):
        """
        Define the data passed during the initialization of the element.
        """
        return self.node().package_name

    @classmethod
    def parseInitializationData(cls, data):
        """
        Parse the serialized initialization data.
        """
        return unreal.EditorAssetLibrary.find_asset_data(data)

    @classmethod
    def test(cls, assetData, _):
        """
        Test if the input contains a unreal asset object.
        """
        if not unrealAvailable:
            return False

        return isinstance(assetData, unreal.AssetData)


# registration
Element.register(
    'unrealSceneNode',
    UnrealSceneNodeElement
)
