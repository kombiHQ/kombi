from .OiioElement import OiioElement

class DpxElement(OiioElement):
    """
    Dpx element.
    """

    @classmethod
    def test(cls, path, parentElement):
        """
        Test if the path contains an dpx file.
        """
        if not super(DpxElement, cls).test(path, parentElement):
            return False

        return path.suffix[1:] == 'dpx'


# registration
DpxElement.register(
    'dpx',
    DpxElement
)
