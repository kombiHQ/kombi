from .AudioElement import AudioElement

class WavElement(AudioElement):
    """
    Wav element.
    """

    @classmethod
    def test(cls, pathHolder, parentElement):
        """
        Test if the path holder contains a wav file.
        """
        if not super(WavElement, cls).test(pathHolder, parentElement):
            return False

        return pathHolder.ext() == 'wav'


# registration
WavElement.register(
    'wav',
    WavElement
)
