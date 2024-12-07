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
    def test(cls, pathHolder, parentElement):
        """
        Test if the path holder contains a fbx file.
        """
        if not super(Exchange3dDataElement, cls).test(pathHolder, parentElement):
            return False

        return pathHolder.ext() == 'fbx'


# registering element
FbxElement.register(
    'fbxScene',
    FbxElement
)
