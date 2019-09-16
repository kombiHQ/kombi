from ..FileCrawler import FileCrawler

class SceneCrawler(FileCrawler):
    """
    Abstracted scene crawler.
    """

    def __init__(self, *args, **kwargs):
        """
        Create a Scene object.
        """
        super(SceneCrawler, self).__init__(*args, **kwargs)

        self.setVar('category', 'scene')

    @classmethod
    def extensions(cls):
        """
        Return the list of available extensions, to be implemented by derived classes.
        """
        raise NotImplementedError
