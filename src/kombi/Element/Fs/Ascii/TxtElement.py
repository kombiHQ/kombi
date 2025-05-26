from .AsciiElement import AsciiElement

class TxtElement(AsciiElement):
    """
    Txt element.
    """

    @classmethod
    def test(cls, path, parentElement):
        """
        Test if the path contains a txt file.
        """
        if not super(AsciiElement, cls).test(path, parentElement):
            return False

        return path.suffix[1:] in ['txt']


# registration
TxtElement.register(
    'txt',
    TxtElement
)
