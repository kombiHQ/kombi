from .ExrRenderInfoCrate import ExrRenderInfoCrate

class TurntableInfoCrate(ExrRenderInfoCrate):
    """
    Custom infoCrate used to detect turntable renders.
    """

    def __init__(self, *args, **kwargs):
        """
        Create a TurntableInfoCrate object.
        """
        super(TurntableInfoCrate, self).__init__(*args, **kwargs)

        parts = self.var("name").split("_")

        # Add the job var once job names on disk match job code names in shotgun
        self.setVar('assetName', parts[1], True)
        self.setVar('step', parts[2], True)
        self.setVar('variant', parts[3], True)
        self.setVar('pass', parts[4], True)
        self.setVar(
            'renderName',
            '{}-{}-{}'.format(
                self.var('assetName'),
                self.var('variant'),
                self.var('pass')
            ),
            True
        )

    @classmethod
    def test(cls, pathHolder, parentInfoCrate):
        """
        Test if the path holder contains a turntable.
        """
        if not super(TurntableInfoCrate, cls).test(pathHolder, parentInfoCrate):
            return False

        renderType = pathHolder.baseName().split(".")[0].split("_")[-1]

        return renderType == "tt"


# registering infoCrate
TurntableInfoCrate.register(
    'turntable',
    TurntableInfoCrate
)
