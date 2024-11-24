from kombi.InfoCrate.Fs.Image import ExrInfoCrate
from kombi.InfoCrate.VarExtractor import VarExtractor

class PlateExr(ExrInfoCrate):
    """
    Implements an internal exr plate.

    Alternatively you can use inline infoCrates instead of this implementation,
    please check the example: vendorXPlatesInlineInfoCrates
    """

    # name example: "foo_abc_def.v0001.000001.exr"
    namePattern = "{job:3}_{seq:3}_{shot:3}_v{version:3i}.######.exr"

    def __init__(self, *args, **kwargs):
        """
        Create an internal plate exr infoCrate object.
        """
        super(PlateExr, self).__init__(*args, **kwargs)

        # assigning variables
        self.assignVars(
            VarExtractor(
                self.var('baseName'),
                self.namePattern
            )
        )

    @classmethod
    def test(cls, data, parentInfoCrate=None):
        """
        Return a boolean telling if the input data can become an internal plate exr infoCrate.
        """
        # perform the tests for the base classes
        if super(PlateExr, cls).test(data, parentInfoCrate):
            return VarExtractor(data.baseName(), cls.namePattern).match()

        return False


# registering infoCrate
ExrInfoCrate.register(
    'plateExr',
    PlateExr
)
