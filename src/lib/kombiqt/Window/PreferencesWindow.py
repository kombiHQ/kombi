import os
from Qt import QtWidgets
from kombi.Task import Task
from kombi.Element.Fs.FsElement import FsElement
from ..OptionVisual.IntOptionVisual import IntOptionVisual
from ..Resource import Resource

class PreferencesWindow(QtWidgets.QDialog):
    """
    Kombi preferences window.
    """

    def __init__(self, parent=None):
        """
        Create PreferencesWindow object.
        """
        super().__init__(parent=parent)
        self.setWindowTitle('Preferences')
        self.setStyleSheet(Resource.stylesheet())

        self.__buildWidgets()

    @classmethod
    def popup(cls, *args, **kwargs):
        """
        Display this window as a popup.
        """
        cls(*args, **kwargs).exec_()

    def __buildWidgets(self):
        """
        Build the base widgets.
        """
        mainLayout = QtWidgets.QVBoxLayout()

        # font setting
        self.__fontSizeWidget = IntOptionVisual(Resource.fontSize(), {"min": 8, "max": 40})
        self.__fontSizeWidget.valueChanged.connect(self.__onFontSizeChanged)
        self.__fontPreviewLabelWidget = QtWidgets.QLabel('The quick brown fox jumps over the lazy dog')
        self.__fontPreviewLabelWidget.setObjectName('fontSizePreview')
        mainLayout.addWidget(QtWidgets.QLabel('Font size (default {}):'.format(Resource.fontSize(ignoreUserConfig=True))))
        mainLayout.addWidget(self.__fontSizeWidget)
        mainLayout.addWidget(self.__fontPreviewLabelWidget, 100)
        mainLayout.addSpacing(20)

        # icon size setting
        self.__listIconSizeWidget = IntOptionVisual(Resource.listIconSize(), {"min": 12, "max": 96})
        self.__listIconSizeWidget.valueChanged.connect(self.__onListIconSizeChanged)
        self.__listIconPreviewWidget = QtWidgets.QLabel()
        self.__listIconPreviewWidget.setObjectName('listIconSizePreview')
        self.__onListIconSizeChanged(Resource.listIconSize())

        mainLayout.addWidget(QtWidgets.QLabel('Icon size when listing elements (default {}):'.format(Resource.listIconSize(ignoreUserConfig=True))))
        mainLayout.addWidget(self.__listIconSizeWidget)
        mainLayout.addWidget(self.__listIconPreviewWidget, 100)
        mainLayout.addSpacing(20)

        preferencesDirectoryWidget = QtWidgets.QLabel('<a href="pref">Show preferences directory</a>')
        preferencesDirectoryWidget.linkActivated.connect(self.__onPreferencesDirectoryClicked)
        mainLayout.addWidget(preferencesDirectoryWidget)
        mainLayout.addSpacing(20)

        saveButtonWidget = QtWidgets.QPushButton('Save')
        saveButtonWidget.clicked.connect(self.__onSave)
        mainLayout.addWidget(saveButtonWidget)
        self.setLayout(mainLayout)

    def __onPreferencesDirectoryClicked(self, _):
        """
        Display the preferences directory.
        """
        task = Task.create('revealInFileManager')
        task.add(FsElement.createFromPath(os.path.dirname(Resource.userConfig().filePath())))
        task.output()

    def __onSave(self):
        """
        Save the preferences.
        """
        fontSize = self.__fontSizeWidget.optionValue()
        listIconSize = self.__listIconSizeWidget.optionValue()

        # when font size is the same size as the default one, removing user preference
        if fontSize == Resource.fontSize(ignoreUserConfig=True):
            Resource.userConfig().removeKey('fontSize')
        else:
            Resource.userConfig().setValue('fontSize', fontSize)

        # when list icon size is the same size as the default one, removing user preference
        if listIconSize == Resource.listIconSize(ignoreUserConfig=True):
            Resource.userConfig().removeKey('listIconSize')
        else:
            Resource.userConfig().setValue('listIconSize', listIconSize)

        QtWidgets.QMessageBox.information(
            self,
            "Preferences saved",
            "Your changes will take effect the next time you restart the application!",
            QtWidgets.QMessageBox.Ok
        )

        self.close()

    def __onFontSizeChanged(self, value):
        """
        Triggered when the font size input is changed.
        """
        self.__fontPreviewLabelWidget.setStyleSheet(f'font-size: {value}px')

    def __onListIconSizeChanged(self, value):
        """
        Triggered when the list icon size input is changed.
        """
        self.__listIconPreviewWidget.setPixmap(Resource.pixmap('icons/elements/base.png', width=value, height=value))
