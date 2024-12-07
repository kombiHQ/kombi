from ..FileElement import FileElement

class Exchange3dDataElement(FileElement):
    """
    Abstracted exchange 3d Data element.
    """

    def __init__(self, *args, **kwargs):
        """
        Create an Exchange3dDataElement object.
        """
        super(Exchange3dDataElement, self).__init__(*args, **kwargs)

        self.setVar('category', 'exchange3dData')

        # setting icon
        self.setTag('icon', 'icons/elements/geo.png')

    @classmethod
    def extensions(cls):
        """
        Return the list of available extensions, to be implemented by derived classes.
        """
        raise NotImplementedError
