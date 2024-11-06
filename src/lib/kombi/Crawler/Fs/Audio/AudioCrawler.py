from ..FileCrawler import FileCrawler

class AudioCrawler(FileCrawler):
    """
    Abstracted audio crawler.
    """

    def __init__(self, *args, **kwargs):
        """
        Create a audio crawler.
        """
        super(AudioCrawler, self).__init__(*args, **kwargs)

        self.setVar('category', 'audio')

        # setting a audio tag
        self.setTag(
            'audio',
            self.pathHolder().baseName()
        )
