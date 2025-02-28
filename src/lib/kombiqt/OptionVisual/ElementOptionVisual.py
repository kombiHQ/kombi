from Qt import QtWidgets
from .OptionVisual import OptionVisual
from ..Element.ElementsLevelNavigationWidget import ElementsLevelNavigationWidget
from ..Element.ElementViewer import ElementViewer
from kombi.Element import Element

class ElementOptionVisual(OptionVisual):
    """
    Implement the widget for an element option.
    """
    __defaultPreviewHeight = 240

    def __init__(self, optionValue, uiHints=None):
        """
        Create ElementOptionVisual object.
        """
        super().__init__(optionValue, uiHints)

        self.__buildWidget()

    def __buildWidget(self):
        """
        Implement the widget.
        """
        mainLayout = QtWidgets.QVBoxLayout()
        mainLayout.setContentsMargins(2, 2, 2, 2)
        self.setLayout(mainLayout)

        self.__mainWidget = ElementsLevelNavigationWidget(showBookmarks=False)
        if self.optionValue():
            self.__mainWidget.setElements([self.optionValue()])

        # preview support
        if self.uiHints().get('preview'):
            previewTag = self.uiHints().get('previewTag', 'previewFilePath')
            elementViewerWidget = ElementViewer([], previewTag)

            # by default lets it fill the whole width
            width = self.uiHints().get('previewWidth', 0)
            if width:
                elementViewerWidget.setFixedWidth(width)

            height = self.uiHints().get('previewHeight', self.__defaultPreviewHeight)
            elementViewerWidget.setFixedHeight(height)
            if self.optionValue():
                elementViewerWidget.setElements([self.optionValue()])
            mainLayout.addWidget(elementViewerWidget, 100)
        mainLayout.addWidget(self.__mainWidget)


OptionVisual.register('element', ElementOptionVisual)
OptionVisual.registerFallbackDefaultVisual('element', Element)
OptionVisual.registerExample('element', 'preview', None, {'preview': True, 'previewHeight': 180})
