from .AudioInfoCrate import AudioInfoCrate

class WavInfoCrate(AudioInfoCrate):
    """
    Wav infoCrate.
    """

    @classmethod
    def test(cls, pathHolder, parentInfoCrate):
        """
        Test if the path holder contains a wav file.
        """
        if not super(WavInfoCrate, cls).test(pathHolder, parentInfoCrate):
            return False

        return pathHolder.ext() == 'wav'


# registration
WavInfoCrate.register(
    'wav',
    WavInfoCrate
)
