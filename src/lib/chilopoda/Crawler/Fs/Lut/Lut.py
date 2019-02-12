from ..Ascii import Xml

class Lut(Xml):
    """
    Abstracted lut crawler.
    """

    def __init__(self, *args, **kwargs):
        """
        Create a lut crawler.
        """
        super(Lut, self).__init__(*args, **kwargs)

        self.setVar('category', 'lut')

        # setting a lut tag
        self.setTag(
            'lut',
            self.pathHolder().baseName()
        )
