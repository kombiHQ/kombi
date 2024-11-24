from .OiioInfoCrate import OiioInfoCrate

class DpxInfoCrate(OiioInfoCrate):
    """
    Dpx infoCrate.
    """

    @classmethod
    def test(cls, pathHolder, parentInfoCrate):
        """
        Test if the path holder contains an dpx file.
        """
        if not super(DpxInfoCrate, cls).test(pathHolder, parentInfoCrate):
            return False

        return pathHolder.ext() == 'dpx'


# registration
DpxInfoCrate.register(
    'dpx',
    DpxInfoCrate
)
