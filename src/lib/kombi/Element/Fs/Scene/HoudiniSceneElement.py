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
    def test(cls, pathHolder, parentElement):
        """
        Test if the path holder contains a houdini scene.
        """
        if not super(SceneElement, cls).test(pathHolder, parentElement):
            return False

        return pathHolder.ext() in cls.extensions()


# registering element
HoudiniSceneElement.register(
    'houdiniScene',
    HoudiniSceneElement
)
