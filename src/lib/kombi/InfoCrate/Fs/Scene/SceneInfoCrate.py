from ..FileInfoCrate import FileInfoCrate

class SceneInfoCrate(FileInfoCrate):
    """
    Abstracted scene infoCrate.
    """

    def __init__(self, *args, **kwargs):
        """
        Create a Scene object.
        """
        super(SceneInfoCrate, self).__init__(*args, **kwargs)

        self.setVar('category', 'scene')

    @classmethod
    def extensions(cls):
        """
        Return the list of available extensions, to be implemented by derived classes.
        """
        raise NotImplementedError
