from ..FileElement import FileElement

class AsciiElement(FileElement):
    """
    Abstracted ascii element.
    """

    def __init__(self, *args, **kwargs):
        """
        Create a ascii element.
        """
        super(AsciiElement, self).__init__(*args, **kwargs)
        self.__parsedContents = None

        # setting icon
        self.setTag('icon', 'icons/elements/ascii.png')

        self.setVar('category', 'ascii')

    def _runParser(self):
        """
        For re-implementation: Needs to return the parsed data.
        """
        f = open(self.var('filePath'), 'r')
        contents = f.read()
        f.close()
        return contents

    def contents(self):
        """
        Return the parsed contents.
        """
        if not self.__parsedContents:
            self.__parsedContents = self._runParser()

        return self.__parsedContents
