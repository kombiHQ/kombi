from .SceneInfoCrate import SceneInfoCrate

class MayaSceneInfoCrate(SceneInfoCrate):
    """
    InfoCrate used to detect maya scenes.
    """

    @classmethod
    def extensions(cls):
        """
        Return the list of available extensions for the maya scene.
        """
        return ['ma', 'mb']

    @classmethod
    def test(cls, pathHolder, parentInfoCrate):
        """
        Test if the path holder contains a Maya scene.
        """
        if not super(SceneInfoCrate, cls).test(pathHolder, parentInfoCrate):
            return False

        return pathHolder.ext() in cls.extensions()


# registering infoCrate
MayaSceneInfoCrate.register(
    'mayaScene',
    MayaSceneInfoCrate
)
