from .OiioInfoCrate import OiioInfoCrate

class ExrInfoCrate(OiioInfoCrate):
    """
    Exr infoCrate.
    """

    @classmethod
    def test(cls, pathHolder, parentInfoCrate):
        """
        Test if the path holder contains an exr file.
        """
        if not super(ExrInfoCrate, cls).test(pathHolder, parentInfoCrate):
            return False

        return pathHolder.ext() == 'exr'


# registration
ExrInfoCrate.register(
    'exr',
    ExrInfoCrate
)
