import os
import sys
from glob import glob
from Qt import QtCore, QtGui

def _resolveResoucesLocation():
    """
    Utility to resolve the resources location.
    """
    dataUI = ("data", "ui")
    rootLocation = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    deployedLocation = os.path.join(rootLocation, *dataUI)
    if os.path.exists(deployedLocation):
        return deployedLocation

    # dev location
    return os.path.join(os.path.dirname(rootLocation), *dataUI)

class Resource(object):
    """
    Utility class used to load resources used by the interface.
    """

    __cache = {}
    __resourcesLocation = _resolveResoucesLocation()
    __defaultFontName = os.environ.get('KOMBI_UI_DEFAULT_FONT_NAME', 'Ubuntu')
    __defaultMonospaceFontName = os.environ.get('KOMBI_UI_DEFAULT_MONOSPACE_FONT_NAME', 'JetBrains Mono')
    __defaultFontSize = os.environ.get('KOMBI_UI_DEFAULT_FONT_SIZE', '13')
    __loadedFont = False
    __loadedMonospaceFont = False

    @classmethod
    def fontName(cls):
        """
        Return the default font name.
        """
        if not cls.__loadedFont:
            cls.loadFonts()
            cls.__loadedFont = True

            fontFound = False
            database = QtGui.QFontDatabase()
            for family in database.families():
                if cls.__defaultFontName == family:
                    fontFound = True
                    break

            if not fontFound:
                sys.stderr.write(f'Could not load kombi default font: {cls.__defaultFontName}\n')
                sys.stderr.flush()

        return cls.__defaultFontName

    @classmethod
    def monospaceFontName(cls):
        """
        Return the default monospace font name.
        """
        if not cls.__loadedMonospaceFont:
            cls.loadFonts()
            cls.__loadedMonospaceFont = True

            fontFound = False
            database = QtGui.QFontDatabase()
            for family in database.families():
                if cls.__defaultMonospaceFontName == family:
                    fontFound = True
                    break

            if not fontFound:
                sys.stderr.write(f'Could not load kombi default monospace font: {cls.__defaultMonospaceFontName}\n')
                sys.stderr.flush()

        return cls.__defaultMonospaceFontName

    @classmethod
    def fontSize(cls):
        """
        Return the default font size.
        """
        assert cls.__defaultFontSize.isdigit(), 'Invalid font size assigned to KOMBI_UI_DEFAULT_FONT_SIZE'
        return int(cls.__defaultFontSize)

    @classmethod
    def qmovie(cls, name):
        """
        Load and return a qmovie (animated gif) based on the input name.
        """
        if "qmovie" not in cls.__cache:
            cls.__cache["qmovie"] = {}

        if name not in cls.__cache["qmovie"]:
            resourceLocation = os.path.join(cls.__resourcesLocation, name)
            if not os.path.exists(resourceLocation):
                resourceLocation = name

            cls.__cache["qmovie"][name] = QtGui.QMovie(resourceLocation)

        return cls.__cache["qmovie"][name]

    @classmethod
    def icon(cls, name):
        """
        Load and return an icon based on the input name.
        """
        if "icon" not in cls.__cache:
            cls.__cache["icon"] = {}

        if name not in cls.__cache["icon"]:
            resourceLocation = os.path.join(cls.__resourcesLocation, name)
            if not os.path.exists(resourceLocation):
                resourceLocation = name

            cls.__cache["icon"][name] = QtGui.QIcon(resourceLocation)

        return cls.__cache["icon"][name]

    @classmethod
    def pixmap(cls, name, width=None, height=None):
        """
        Load and return a pixmap based on the input name.
        """
        if "pixmap" not in cls.__cache:
            cls.__cache["pixmap"] = {}

        key = (name, width, height)
        if key not in cls.__cache["pixmap"]:
            resourceLocation = os.path.join(cls.__resourcesLocation, name)
            if not os.path.exists(resourceLocation):
                resourceLocation = name

            cls.__cache["pixmap"][key] = QtGui.QPixmap(resourceLocation)

            # resizing pixmap
            if width or height:
                cls.__cache["pixmap"][key] = cls.__cache["pixmap"][key].scaled(
                    width,
                    height,
                    QtCore.Qt.IgnoreAspectRatio,
                    QtCore.Qt.SmoothTransformation
                )

        return cls.__cache["pixmap"][key]

    @classmethod
    def mergePixmap(cls, pixmapA, pixmapB, resultAsIcon=False):
        """
        Merge two pixmaps.
        """
        if "mergedPixmap" not in cls.__cache:
            cls.__cache["mergedPixmap"] = {}

        key = (pixmapA.cacheKey(), pixmapB.cacheKey(), resultAsIcon)
        if key not in cls.__cache["mergedPixmap"]:
            mergedPixmap = QtGui.QPixmap(pixmapA.size())
            mergedPixmap.fill(QtCore.Qt.transparent)

            painter = QtGui.QPainter(mergedPixmap)
            painter.drawPixmap(0, 0, pixmapA)
            painter.drawPixmap(0, 0, pixmapB)
            painter.end()

            cls.__cache["mergedPixmap"][key] = QtGui.QIcon(mergedPixmap) if resultAsIcon else mergedPixmap

        return cls.__cache["mergedPixmap"][key]

    @classmethod
    def loadFonts(cls):
        """
        Load the custom fonts to the runtime.
        """
        for ttfFilePath in glob(os.path.join(cls.__resourcesLocation, "fonts", "*.ttf")):
            QtGui.QFontDatabase.addApplicationFont(ttfFilePath)

    @classmethod
    def stylesheet(cls):
        """
        Return the main stylesheet.
        """
        if "stylesheet" not in cls.__cache:
            styleSheetFile = os.path.join(cls.__resourcesLocation, "darkstyle", "darkstyle.qss")

            styleSheetContents = None
            with open(styleSheetFile, "r") as f:
                styleSheetContents = f.read().replace(
                    "darkstyle/",
                    '{0}/'.format(
                        os.path.dirname(styleSheetFile).replace('\\', '/')
                    )
                )
            cls.__cache['stylesheet'] = styleSheetContents.replace(
                '<fontSize>',
                str(cls.fontSize())
            ).replace(
                '<fontName>',
                cls.fontName()
            ).replace(
                '<monospaceFontName>',
                cls.monospaceFontName()
            )

        return cls.__cache['stylesheet']
