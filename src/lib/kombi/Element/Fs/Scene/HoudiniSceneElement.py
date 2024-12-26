from .SceneElement import SceneElement

class HoudiniSceneElement(SceneElement):
    """
    Element used to detect houdini scenes.
    """

    @classmethod
    def extensions(cls):
        """
        Return the list of available extensions for the houdini scene.
        """
        return ['hip']

    @classmethod
    def test(cls, path, parentElement):
        """
        Test if the path contains a houdini scene.
        """
        if not super(SceneElement, cls).test(path, parentElement):
            return False

        return path.suffix[1:] in cls.extensions()


# registering element
HoudiniSceneElement.register(
    'houdiniScene',
    HoudiniSceneElement
)
