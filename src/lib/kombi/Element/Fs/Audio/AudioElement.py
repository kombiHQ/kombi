from ..FileElement import FileElement

class AudioElement(FileElement):
    """
    Abstracted audio element.
    """

    def __init__(self, *args, **kwargs):
        """
        Create a audio element.
        """
        super(AudioElement, self).__init__(*args, **kwargs)

        self.setVar('category', 'audio')

        # setting a audio tag
        self.setTag('audio', self.pathHolder().baseName())

        # setting icon
        self.setTag('icon', 'icons/elements/audio.png')
