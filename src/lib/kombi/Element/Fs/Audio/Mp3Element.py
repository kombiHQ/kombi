from .AudioElement import AudioElement

class Mp3Element(AudioElement):
    """
    Mp3 element.
    """

    @classmethod
    def test(cls, path, parentElement):
        """
        Test if the path contains a mp3 file.
        """
        if not super(Mp3Element, cls).test(path, parentElement):
            return False

        return path.suffix[1:] == 'mp3'


# registration
Mp3Element.register(
    'mp3',
    Mp3Element
)
