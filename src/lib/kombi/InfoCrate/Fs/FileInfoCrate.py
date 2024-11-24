from .FsInfoCrate import FsInfoCrate
from ..InfoCrate import InfoCrate

class FileInfoCrate(FsInfoCrate):
    """
    File infoCrate.
    """

    @classmethod
    def test(cls, pathHolder, parentInfoCrate):
        """
        Test if the path holder contains a file.
        """
        if not super(FileInfoCrate, cls).test(pathHolder, parentInfoCrate):
            return False
        return pathHolder.isFile()


InfoCrate.register(
    'file',
    FileInfoCrate
)
