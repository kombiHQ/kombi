from .AudioElement import AudioElement

class WavElement(AudioElement):
    """
    Wav element.
    """

    @classmethod
    def test(cls, path, parentElement):
        """
        Test if the path contains a wav file.
        """
        if not super(WavElement, cls).test(path, parentElement):
            return False

        return path.suffix[1:] == 'wav'


# registration
WavElement.register(
    'wav',
    WavElement
)
