from .OiioInfoCrate import OiioInfoCrate

class PngInfoCrate(OiioInfoCrate):
    """
    Png infoCrate.
    """

    @classmethod
    def test(cls, pathHolder, parentInfoCrate):
        """
        Test if the path holder contains an png file.
        """
        if not super(PngInfoCrate, cls).test(pathHolder, parentInfoCrate):
            return False

        return pathHolder.ext() == 'png'


# registration
PngInfoCrate.register(
    'png',
    PngInfoCrate
)
