from ..Image import OiioInfoCrate

class TextureInfoCrate(OiioInfoCrate):
    """
    Custom infoCrate used to detect textures.

    This infoCrate is only meant to be used only as inheritance. Therefore,
    when implementing the test call the super class passing the extra parameter
    enable=True

    ```python
    class YourClawler(TextureInfoCrate):
        @classmethod
        def test(cls, pathHolder, parentInfoCrate):
            if not super(YourClawler, cls).test(pathHolder, parentInfoCrate, enable=True):
                return False

            # your implementation...
            # return True
    ```
    """

    __groupTextures = True

    def __init__(self, *args, **kwargs):
        """
        Create a texture object.
        """
        super(TextureInfoCrate, self).__init__(*args, **kwargs)

        self.setVar('category', 'texture')

        parts = self.var("name").split("_")

        self.setVar("assetName", parts[0])
        self.setVar("mapType", parts[1])
        self.setVar("udim", self.__parseUDIM(self.pathHolder()))
        self.setVar("variant", "default")

    def setVar(self, name, value, *args, **kwargs):
        """
        Override setVar to be able to hook when mapType is assigned.
        """
        if name == "mapType":
            value = value.upper()

        super(TextureInfoCrate, self).setVar(name, value, *args, **kwargs)

        # we need to update the group tag name after a change in the
        # assetName or variant
        if self.__groupTextures and name in ['assetName', 'variant']:
            self.__updateGroupTag()

    @classmethod
    def test(cls, pathHolder, parentInfoCrate, enable=False):
        """
        Test if the path holder contains a texture exr or tif file.
        """
        if not enable:
            return False

        if not super(TextureInfoCrate, cls).test(pathHolder, parentInfoCrate):
            return False

        if pathHolder.ext() not in ['exr', 'tif']:
            return False

        return (cls.__parseUDIM(pathHolder) is not None)

    @classmethod
    def __parseUDIM(cls, pathHolder):
        """
        Return an integer about the udim found in the texture name (or none).
        """
        name = pathHolder.baseName()[:-(len(pathHolder.ext()) + 1)]
        parts = name.split("_")

        udim = None
        if len(parts) >= 3:
            # detecting based on mari UDIM:
            # http://bneall.blogspot.ca/p/udim-guide.html
            # assetName_textureType_1001.exr
            if parts[2].isdigit() and len(parts[2]) == 4:
                udim = int(parts[2])

            # detecting based on mudbox:
            # assetName_textureType_u1_v1.exr (starts from 1)
            elif len(parts) >= 4 and parts[2].startswith("u") and parts[3].startswith("v"):
                u = int(parts[2][1:]) - 1
                v = int(parts[3][1:]) - 1
                udim = 1000 + (u + 1) + (v * 10)
        return udim

    def __updateGroupTag(self):
        """
        Update the group tag.
        """
        if 'assetName' not in self.varNames() or 'variant' not in self.varNames():
            return

        self.setTag(
            "group",
            "{}-{}".format(
                self.var('assetName'),
                self.var('variant')
            )
        )


# registering infoCrate
TextureInfoCrate.register(
    'texture',
    TextureInfoCrate
)
