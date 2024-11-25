from .OiioElement import OiioElement

class ExrElement(OiioElement):
    """
    Exr element.
    """

    @classmethod
    def test(cls, pathHolder, parentElement):
        """
        Test if the path holder contains an exr file.
        """
        if not super(ExrElement, cls).test(pathHolder, parentElement):
            return False

        return pathHolder.ext() == 'exr'


# registration
ExrElement.register(
    'exr',
    ExrElement
)
