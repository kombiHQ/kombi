from .AudioCrawler import AudioCrawler

class WavCrawler(AudioCrawler):
    """
    Wav crawler.
    """

    @classmethod
    def test(cls, pathHolder, parentCrawler):
        """
        Test if the path holder contains a wav file.
        """
        if not super(WavCrawler, cls).test(pathHolder, parentCrawler):
            return False

        return pathHolder.ext() == 'wav'


# registration
WavCrawler.register(
    'wav',
    WavCrawler
)
