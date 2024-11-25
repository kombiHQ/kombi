from .AsciiElement import AsciiElement

class TxtElement(AsciiElement):
    """
    Txt element.
    """

    @classmethod
    def test(cls, pathHolder, parentElement):
        """
        Test if the path holder contains a txt file.
        """
        if not super(AsciiElement, cls).test(pathHolder, parentElement):
            return False

        return pathHolder.ext() in ['txt']


# registration
TxtElement.register(
    'txt',
    TxtElement
)
