import os
import sys
from ..FileElement import FileElement

class AsciiElement(FileElement):
    """
    Abstracted ascii element.
    """
    __detailsMaxSize = int(os.environ.get('KOMBI_ELEMENT_DETAILS_MAX_SIZE', 10 * 1024))

    def __init__(self, *args, **kwargs):
        """
        Create a ascii element.
        """
        super(AsciiElement, self).__init__(*args, **kwargs)
        self.__parsedContents = None

        # setting icon
        self.setTag('icon', 'icons/elements/ascii.png')
        self.setVar('category', 'ascii')

        # the 'details' tag is used to show additional information when an element is selected
        # and the browser's info panel is activated. It should be set to the name of a method (as a string).
        # If the method returns a QWidget, that widget is used as the details view. Otherwise, a default
        # OptionValue widget is automatically generated to display the data.
        self.setTag('details', 'computeDetails')

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

    def computeDetails(self):
        """
        Compute the details content display in the browser.
        """
        dataSize = self.dataSize(self.contents())
        if dataSize <= self.__detailsMaxSize:
            return self.contents()

        return f"Cannot display details (exceeds {self.__detailsMaxSize} bytes)."

    @classmethod
    def dataSize(cls, data):
        """
        Utility method to return the data size in bytes.
        """
        size = sys.getsizeof(data)
        if isinstance(data, dict):
            size += sum(cls.dataSize(key) + cls.dataSize(value) for key, value in data.items())
        elif isinstance(data, (list, tuple, set)):
            size += sum(cls.dataSize(item) for item in data)
        return size
