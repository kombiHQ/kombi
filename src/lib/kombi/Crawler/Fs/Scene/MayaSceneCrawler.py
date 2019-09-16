from .SceneCrawler import SceneCrawler

class MayaSceneCrawler(SceneCrawler):
    """
    Crawler used to detect maya scenes.
    """

    @classmethod
    def extensions(cls):
        """
        Return the list of available extensions for the maya scene.
        """
        return ['ma', 'mb']

    @classmethod
    def test(cls, pathHolder, parentCrawler):
        """
        Test if the path holder contains a Maya scene.
        """
        if not super(SceneCrawler, cls).test(pathHolder, parentCrawler):
            return False

        return pathHolder.ext() in cls.extensions()


# registering crawler
MayaSceneCrawler.register(
    'mayaScene',
    MayaSceneCrawler
)
