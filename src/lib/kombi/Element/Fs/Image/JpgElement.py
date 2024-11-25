from .OiioElement import OiioElement

class JpgElement(OiioElement):
    """
    Jpg element.
    """

    @classmethod
    def test(cls, pathHolder, parentElement):
        """
        Test if the path holder contains an jpg file.
        """
        if not super(JpgElement, cls).test(pathHolder, parentElement):
            return False

        return pathHolder.ext() == 'jpg'


# registration
JpgElement.register(
    'jpg',
    JpgElement
)
