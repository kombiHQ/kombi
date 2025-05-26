from ..FileElement import FileElement

class SceneElement(FileElement):
    """
    Abstracted scene element.
    """

    def __init__(self, *args, **kwargs):
        """
        Create a Scene object.
        """
        super(SceneElement, self).__init__(*args, **kwargs)

        self.setVar('category', 'scene')

        # setting icon
        self.setTag('icon', 'icons/elements/scene.png')

    @classmethod
    def extensions(cls):
        """
        Return the list of available extensions, to be implemented by derived classes.
        """
        raise NotImplementedError
