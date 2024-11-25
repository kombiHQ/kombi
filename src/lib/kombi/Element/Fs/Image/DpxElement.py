from .OiioElement import OiioElement

class DpxElement(OiioElement):
    """
    Dpx element.
    """

    @classmethod
    def test(cls, pathHolder, parentElement):
        """
        Test if the path holder contains an dpx file.
        """
        if not super(DpxElement, cls).test(pathHolder, parentElement):
            return False

        return pathHolder.ext() == 'dpx'


# registration
DpxElement.register(
    'dpx',
    DpxElement
)
