from .FsElement import FsElement
from ..Element import Element

class FileElement(FsElement):
    """
    File element.
    """

    @classmethod
    def test(cls, path, parentElement):
        """
        Test if the path contains a file.
        """
        if not super(FileElement, cls).test(path, parentElement):
            return False
        return path.is_file()


Element.register(
    'file',
    FileElement
)
