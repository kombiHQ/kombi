from .OiioInfoCrate import OiioInfoCrate

class TiffInfoCrate(OiioInfoCrate):
    """
    Tiff infoCrate.
    """

    @classmethod
    def test(cls, pathHolder, parentInfoCrate):
        """
        Test if the path holder contains an tiff file.
        """
        if not super(TiffInfoCrate, cls).test(pathHolder, parentInfoCrate):
            return False

        return pathHolder.ext() in ('tif', 'tiff')


# registration
TiffInfoCrate.register(
    'tiff',
    TiffInfoCrate
)
