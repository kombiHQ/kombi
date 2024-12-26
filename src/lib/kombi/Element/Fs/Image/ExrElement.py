from .OiioElement import OiioElement

class ExrElement(OiioElement):
    """
    Exr element.
    """

    @classmethod
    def test(cls, path, parentElement):
        """
        Test if the path contains an exr file.
        """
        if not super(ExrElement, cls).test(path, parentElement):
            return False

        return path.suffix[1:] == 'exr'


# registration
ExrElement.register(
    'exr',
    ExrElement
)
