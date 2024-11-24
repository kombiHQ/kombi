from .ExrRenderInfoCrate import ExrRenderInfoCrate

class ShotRenderInfoCrate(ExrRenderInfoCrate):
    """
    Custom infoCrate used to detect renders for shots.
    """

    def __init__(self, *args, **kwargs):
        """
        Create a Render object.
        """
        super(ShotRenderInfoCrate, self).__init__(*args, **kwargs)

        parts = self.var("name").split("_")
        locationParts = parts[0].split("-")

        # Add the job var once job names on disk match job code names in shotgun
        self.setVar('seq', locationParts[1], True)
        self.setVar('shot', parts[0], True)
        self.setVar('step', parts[1], True)
        self.setVar('pass', parts[2], True)
        self.setVar(
            'renderName',
            '{}-{}'.format(
                self.var('step'),
                self.var('pass')
            ),
            True
        )

    @classmethod
    def test(cls, pathHolder, parentInfoCrate):
        """
        Test if the path holder contains a shot render.
        """
        if not super(ShotRenderInfoCrate, cls).test(pathHolder, parentInfoCrate):
            return False

        renderType = pathHolder.baseName().split(".")[0].split("_")[-1]

        return renderType == "sr"


# registering infoCrate
ShotRenderInfoCrate.register(
    'shotRender',
    ShotRenderInfoCrate
)
