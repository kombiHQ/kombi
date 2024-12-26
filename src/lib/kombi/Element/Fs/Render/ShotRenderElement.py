from .ExrRenderElement import ExrRenderElement

class ShotRenderElement(ExrRenderElement):
    """
    Custom element used to detect renders for shots.
    """

    def __init__(self, *args, **kwargs):
        """
        Create a Render object.
        """
        super(ShotRenderElement, self).__init__(*args, **kwargs)

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

        # setting icon
        self.setTag('icon', 'icons/elements/render.png')

    @classmethod
    def test(cls, path, parentElement):
        """
        Test if the path contains a shot render.
        """
        if not super(ShotRenderElement, cls).test(path, parentElement):
            return False

        renderType = path.name.split(".")[0].split("_")[-1]

        return renderType == "sr"


# registering element
ShotRenderElement.register(
    'shotRender',
    ShotRenderElement
)
