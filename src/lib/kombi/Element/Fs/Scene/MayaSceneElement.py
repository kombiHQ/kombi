from .SceneElement import SceneElement

class MayaSceneElement(SceneElement):
    """
    Element used to detect maya scenes.
    """

    @classmethod
    def extensions(cls):
        """
        Return the list of available extensions for the maya scene.
        """
        return ['ma', 'mb']

    @classmethod
    def test(cls, pathHolder, parentElement):
        """
        Test if the path holder contains a Maya scene.
        """
        if not super(SceneElement, cls).test(pathHolder, parentElement):
            return False

        return pathHolder.ext() in cls.extensions()


# registering element
MayaSceneElement.register(
    'mayaScene',
    MayaSceneElement
)
