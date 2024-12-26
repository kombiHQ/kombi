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
    def test(cls, path, parentElement):
        """
        Test if the path contains a Maya scene.
        """
        if not super(SceneElement, cls).test(path, parentElement):
            return False

        return path.suffix[1:] in cls.extensions()


# registering element
MayaSceneElement.register(
    'mayaScene',
    MayaSceneElement
)
