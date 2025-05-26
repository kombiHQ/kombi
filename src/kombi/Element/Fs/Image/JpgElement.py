from .OiioElement import OiioElement

class JpgElement(OiioElement):
    """
    Jpg element.
    """

    @classmethod
    def test(cls, path, parentElement):
        """
        Test if the path holder contains an jpg file.
        """
        if not super(JpgElement, cls).test(path, parentElement):
            return False

        return path.suffix[1:] == 'jpg'


# registration
JpgElement.register(
    'jpg',
    JpgElement
)
