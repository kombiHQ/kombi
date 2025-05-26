from .Exchange3dDataElement import Exchange3dDataElement

class FbxElement(Exchange3dDataElement):
    """
    Element used to detect fbx files.
    """

    def __init__(self, *args, **kwargs):
        """
        Create a fbx object.
        """
        super(FbxElement, self).__init__(*args, **kwargs)

        # setting icon
        icon = 'icons/elements/geo.png'
        if 'camera' in self.var('name').lower():
            icon = 'icons/elements/camera.png'
        self.setTag('icon', icon)

    @classmethod
    def test(cls, path, parentElement):
        """
        Test if the path contains a fbx file.
        """
        if not super(Exchange3dDataElement, cls).test(path, parentElement):
            return False

        return path.suffix[1:] == 'fbx'


# registering element
FbxElement.register(
    'fbxScene',
    FbxElement
)
