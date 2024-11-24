from ..FileInfoCrate import FileInfoCrate

class AudioInfoCrate(FileInfoCrate):
    """
    Abstracted audio infoCrate.
    """

    def __init__(self, *args, **kwargs):
        """
        Create a audio infoCrate.
        """
        super(AudioInfoCrate, self).__init__(*args, **kwargs)

        self.setVar('category', 'audio')

        # setting a audio tag
        self.setTag(
            'audio',
            self.pathHolder().baseName()
        )
