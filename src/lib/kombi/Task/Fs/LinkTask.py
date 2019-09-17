import os
import platform
from ..Task import Task, TaskError

class LinkTaskTargetDirectoryError(TaskError):
    """Link Target Directory Error."""

class LinkTask(Task):
    """
    Links (hardlink or symlink) a file to the target file path.
    """

    __defaultLinkType = "hardlink"
    __kernelDll = None

    def __init__(self, *args, **kwargs):
        """
        Create a Link task.
        """
        super(LinkTask, self).__init__(*args, **kwargs)

        self.setOption('type', self.__defaultLinkType)
        self.setMetadata('dispatch.split', True)
        self.setMetadata('dispatch.splitSize', 20)

    def _perform(self):
        """
        Perform the task.
        """
        assert self.option('type') in ('hardlink', 'symlink'), "Invalid link type {}".format(self.option())

        for crawler in self.crawlers():
            filePath = self.target(crawler)

            # trying to create the directory automatically in case it does not exist
            try:
                os.makedirs(os.path.dirname(filePath))
            except OSError:
                pass

            # linking the file to the new target
            sourceFilePath = crawler.var('filePath')
            targetFilePath = filePath

            # Check if the target path already exists, if it is file remove it else raise an exception
            if os.path.isfile(targetFilePath):
                os.remove(targetFilePath)
            elif os.path.isdir(targetFilePath):
                raise LinkTaskTargetDirectoryError(
                    'Target directory already exists {}'.format(targetFilePath)
                )

            # linking
            if platform.system() == "Windows":
                self.__linkOnWindows(
                    sourceFilePath,
                    targetFilePath
                )
            else:
                self.__linkOnUnix(
                    sourceFilePath,
                    targetFilePath
                )

        # default result based on the target filePath
        return super(LinkTask, self)._perform()

    def __linkOnWindows(self, sourceFilePath, targetFilePath):
        """
        Create a link on windows.
        """
        # loading the kernel dll when necessary
        if self.__kernelDll is None:
            import ctypes
            self.__kernelDll = ctypes.windll.LoadLibrary("kernel32.dll")

        sourceFilePath = os.path.normpath(sourceFilePath)
        targetFilePath = os.path.normpath(targetFilePath)

        # NOTE: creating a symlinks on windows requires additional permissions
        if self.option('type') == "symlink":
            createSymboliclink = ctypes.windll.kernel32.CreateSymbolicLinkW
            createSymboliclink.argtypes = (ctypes.c_wchar_p, ctypes.c_wchar_p, ctypes.c_uint32)
            createSymboliclink.restype = ctypes.c_ubyte
            flags = int(os.path.isdir(sourceFilePath))
            if createSymboliclink(targetFilePath, sourceFilePath, flags) == 0:
                raise ctypes.WinError()

        elif self.option('type') == "hardlink":
            createHardlink = ctypes.windll.kernel32.CreateHardLinkW
            createHardlink.argtypes = (ctypes.c_wchar_p, ctypes.c_wchar_p, ctypes.c_uint32)
            createHardlink.restype = ctypes.c_ubyte
            flags = 0
            if createHardlink(targetFilePath, sourceFilePath, flags) == 0:
                raise ctypes.WinError()

    def __linkOnUnix(self, sourceFilePath, targetFilePath):
        """
        Create a link on unix.
        """
        if self.option('type') == "symlink":
            os.symlink(
                sourceFilePath,
                targetFilePath
            )
        elif self.option('type') == "hardlink":
            os.link(
                sourceFilePath,
                targetFilePath
            )


# registering task
Task.register(
    'link',
    LinkTask
)
