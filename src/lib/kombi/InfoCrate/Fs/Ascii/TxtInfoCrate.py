from .AsciiInfoCrate import AsciiInfoCrate

class TxtInfoCrate(AsciiInfoCrate):
    """
    Txt infoCrate.
    """

    @classmethod
    def test(cls, pathHolder, parentInfoCrate):
        """
        Test if the path holder contains a txt file.
        """
        if not super(AsciiInfoCrate, cls).test(pathHolder, parentInfoCrate):
            return False

        return pathHolder.ext() in ['txt']


# registration
TxtInfoCrate.register(
    'txt',
    TxtInfoCrate
)
