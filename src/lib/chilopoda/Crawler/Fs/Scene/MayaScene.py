from .Scene import Scene

class MayaScene(Scene):
    """
    Crawler used to detect maya scenes.
    """

    def __init__(self, *args, **kwargs):
        """
        Create a MayaScene object.
        """
        super(MayaScene, self).__init__(*args, **kwargs)

    @classmethod
    def extensions(cls):
        """
        Return the list of available extensions for a MayaScene.
        """
        return ['ma', 'mb']

    @classmethod
    def test(cls, pathHolder, parentCrawler):
        """
        Test if the path holder contains a Maya scene.
        """
        if not super(Scene, cls).test(pathHolder, parentCrawler):
            return False

        return pathHolder.ext() in cls.extensions()


# registering crawler
MayaScene.register(
    'mayaScene',
    MayaScene
)
