import os

class PathHolder(object):
    """
    Provides quick access to query information about the path.
    """

    def __init__(self, path):
        """
        Create a path holder object.
        """
        # lazy data
        self.__basename = None
        self.__name = None
        self.__pathExists = None
        self.__isDirectory = None
        self.__size = None
        self.__ext = None

        # setting path
        self.__setPath(path)

    def isDirectory(self):
        """
        Return a boolean telling if the path is a directory.
        """
        if self.__isDirectory is None:
            self.__isDirectory = os.path.isdir(self.path())

        return self.__isDirectory

    def isFile(self):
        """
        Return a boolean telling if the path is a file.
        """
        return not self.isDirectory()

    def ext(self):
        """
        Return the file extension for the path (converts automatically to lowercase).
        """
        if self.__ext is None:
            self.__ext = os.path.splitext(self.path())[-1][1:].lower()

        return self.__ext

    def size(self):
        """
        Return the size of the file.
        """
        if self.__size is None:
            self.__size = os.stat(self.path()).st_size

        return self.__size

    def baseName(self):
        """
        Return the base name about the path.
        """
        if self.__basename is None:
            name = os.path.basename(self.path())
            if not name:
                name = os.sep if os.name == 'posix' else self.path()[:2]

            self.__basename = name

        return self.__basename

    def name(self):
        """
        Return the base name without the extension.
        """
        if self.__name is None:
            self.__name = os.path.splitext(self.baseName())[0]

        return self.__name

    def exists(self):
        """
        Return a boolean telling if the path exists.
        """
        if self.__pathExists is None:
            self.__pathExists = os.path.exists(self.path())

        return self.__pathExists

    def path(self):
        """
        Return the path.
        """
        return self.__path

    def __repr__(self):
        """
        Return a string representation for the path holder.
        """
        return "PathHolder({})".format(self.path())

    def __setPath(self, path):
        """
        Set a path to the path holder.

        @private
        """
        # cleaning any extra "slash" to figure out the basename, for instance
        # slashes after the name
        cleanedPath = path.strip(os.sep)

        if path.startswith(os.sep):
            cleanedPath = os.sep + cleanedPath

        self.__path = cleanedPath
