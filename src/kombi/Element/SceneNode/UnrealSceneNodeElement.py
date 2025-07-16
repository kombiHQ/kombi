import json
import pathlib
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
        super().__init__(str(assetData.package_name), *args, **kwargs)
        self.setVar('fullPath', self.var('name'))
        self.setVar('assetName', str(assetData.asset_name))
        self.setVar('packagePath', str(assetData.package_path))
        self.setVar('nodeType', str(assetData.get_class().get_name()))
        self.setTag('label', self.var('assetName'))

        self.__node = assetData

    def node(self):
        """
        Return the unreal object.
        """
        return self.__node

    def filePath(self):
        """
        Return the file path associated with the asset.
        """
        importData = self.node().get_tag_value('AssetImportData')
        result = ''
        if importData:
            try:
                jsonData = json.loads(importData)
                importedPath = jsonData[0]['RelativeFilename']
            except Exception:
                pass
            else:
                result = unreal.Paths.convert_relative_path_to_full(importedPath)

        return result

    def uassetPath(self):
        """
        Utility method used to return uasset file path.
        """
        contentPath = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_content_dir())
        packageName = str(self.node().package_name)
        if packageName.startswith('/Game/'):
            packageName = packageName[6:]

        return pathlib.Path(contentPath).joinpath(f"{packageName}.uasset").as_posix()

    def select(self, groupedElements=None):
        """
        Select the asset in the content browser.
        """
        elements = [self]
        if groupedElements:
            elements = groupedElements

        unreal.EditorAssetLibrary.sync_browser_to_objects(list(map(lambda x: x.node().package_name, elements)))

    def serializeInitializationData(self):
        """
        Define the data passed during the initialization of the element.
        """
        return str(self.node().package_name)

    @classmethod
    def createFromName(cls, packageName):
        """
        Create a node element based on the package name.
        """
        return Element.create(cls.parseInitializationData(packageName))

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
