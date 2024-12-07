from .Exchange3dDataElement import Exchange3dDataElement

class AbcElement(Exchange3dDataElement):
    """
    Element used to detect abc files.
    """

    @classmethod
    def test(cls, pathHolder, parentElement):
        """
        Test if the path holder contains an abc file.
        """
        if not super(Exchange3dDataElement, cls).test(pathHolder, parentElement):
            return False

        return pathHolder.ext() == 'abc'


# registering element
AbcElement.register(
    'abcScene',
    AbcElement
)
