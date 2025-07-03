import platform
from datetime import datetime
from .FsElement import FsElement
from ..Element import Element

if platform.system() == 'Windows':
    import ctypes
    from ctypes import wintypes
else:
    import pwd
    import grp

class FileElement(FsElement):
    """
    File element.
    """

    def __init__(self, *args, **kwargs):
        """
        Create a file element object.
        """
        super().__init__(*args, **kwargs)

        self.setTag('details', 'computeDetails')

    def var(self, name, *args, **kwargs):
        """
        Return var value using lazy loading implementation for ownerUser, ownerGroup, byteSize and modificationDate.
        """
        if name in ('ownerUser', 'ownerGroup', 'byteSize', 'modificationDate') and name not in self.varNames():
            stat = self.path().stat()
            modificationDate = datetime.fromtimestamp(stat.st_mtime)
            self.setVar('byteSize', stat.st_size)
            self.setVar('modificationDate', modificationDate.strftime('%Y-%m-%d %H:%M:%S'))
            user, group = self.__computeOwner(stat)
            self.setVar('ownerUser', user)
            self.setVar('ownerGroup', group)

        return super().var(name, *args, **kwargs)

    def computeDetails(self):
        """
        Return the information displayed in the Details panel when requested.
        """
        # adding the group (or domain in case of windows) info when it's different from the user
        owner = self.var('ownerUser')
        group = self.var('ownerGroup')
        if group and owner != group:
            owner = f"{owner}/{group}"

        return {
            "sizeMb": self.var('byteSize') / (1024 ** 2),
            "modificationDate": self.var('modificationDate'),
            "owner": owner
        }

    @classmethod
    def test(cls, path, parentElement):
        """
        Test if the path contains a file.
        """
        if not super(FileElement, cls).test(path, parentElement):
            return False
        return cls.cachedPathQuery(path, 'is_file')

    def __computeOwner(self, stat):
        """
        Return the file owner (user and group).
        """
        if platform.system() == 'Windows':
            return self.__computeOwnerWindows()

        # posix
        user = pwd.getpwuid(stat.st_uid).pw_name
        group = grp.getgrgid(stat.st_gid).gr_name

        return (user, group)

    def __computeOwnerWindows(self):
        """
        Return the file owner on Windows.
        """
        lengthNeeded = wintypes.DWORD(0)
        ctypes.windll.advapi32.GetFileSecurityW(
            self.var('filePath'),
            0x00000001,
            None,
            0,
            ctypes.byref(lengthNeeded)
        )

        securityDescriptor = ctypes.create_string_buffer(lengthNeeded.value)
        if not ctypes.windll.advapi32.GetFileSecurityW(
            self.var('filePath'),
            0x00000001,
            securityDescriptor,
            lengthNeeded.value,
            ctypes.byref(lengthNeeded)
        ):
            return ctypes.WinError()

        ownerId = ctypes.c_void_p()
        if not ctypes.windll.advapi32.GetSecurityDescriptorOwner(
            securityDescriptor,
            ctypes.byref(ownerId),
            ctypes.byref(wintypes.BOOL())
        ):
            raise ctypes.WinError()

        name = ctypes.create_unicode_buffer(256)
        domain = ctypes.create_unicode_buffer(256)
        if not ctypes.windll.advapi32.LookupAccountSidW(
            None,
            ownerId,
            name,
            ctypes.byref(wintypes.DWORD(len(name))),
            domain,
            ctypes.byref(wintypes.DWORD(len(domain))),
            ctypes.byref(wintypes.DWORD())
        ):
            raise ctypes.WinError()

        return (name.value, domain.value)


Element.register(
    'file',
    FileElement
)
