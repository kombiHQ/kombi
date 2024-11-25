from .FsElement import FsElement
from ..Element import Element

class FileElement(FsElement):
    """
    File element.
    """

    @classmethod
    def test(cls, pathHolder, parentElement):
        """
        Test if the path holder contains a file.
        """
        if not super(FileElement, cls).test(pathHolder, parentElement):
            return False
        return pathHolder.isFile()


Element.register(
    'file',
    FileElement
)
