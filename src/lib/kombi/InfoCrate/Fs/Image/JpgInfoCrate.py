from .OiioInfoCrate import OiioInfoCrate

class JpgInfoCrate(OiioInfoCrate):
    """
    Jpg infoCrate.
    """

    @classmethod
    def test(cls, pathHolder, parentInfoCrate):
        """
        Test if the path holder contains an jpg file.
        """
        if not super(JpgInfoCrate, cls).test(pathHolder, parentInfoCrate):
            return False

        return pathHolder.ext() == 'jpg'


# registration
JpgInfoCrate.register(
    'jpg',
    JpgInfoCrate
)
