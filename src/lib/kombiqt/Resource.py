import os
from Qt import QtCore, QtGui

class Resource(object):
    """
    Utility class used to load resources used by the interface.
    """

    __cache = {}
    __resourcesLocation = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data", "ui")

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
            cls.__cache['stylesheet'] = styleSheetContents

        return cls.__cache['stylesheet']
