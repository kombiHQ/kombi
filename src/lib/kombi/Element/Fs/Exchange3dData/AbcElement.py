from .Exchange3dDataElement import Exchange3dDataElement

class AbcElement(Exchange3dDataElement):
    """
    Element used to detect abc files.
    """

    @classmethod
    def test(cls, path, parentElement):
        """
        Test if the path contains an abc file.
        """
        if not super(Exchange3dDataElement, cls).test(path, parentElement):
            return False

        return path.suffix[1:] == 'abc'


# registering element
AbcElement.register(
    'abcScene',
    AbcElement
)
