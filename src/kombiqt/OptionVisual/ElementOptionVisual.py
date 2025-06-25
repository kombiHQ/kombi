from Qt import QtWidgets
from .OptionVisual import OptionVisual
from ..Widget.ElementLevelNavigationWidget import ElementLevelNavigationWidget
from ..Widget.ElementViewerWidget import ElementViewerWidget
from kombi.Element import Element
from kombi.Element.Fs.Image import ImageElement

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

        self.__mainWidget = ElementLevelNavigationWidget(showBookmarks=False)
        if self.optionValue():
            self.__mainWidget.setElements([self.optionValue()])

        # preview support
        if self.uiHints().get('preview'):
            previewTag = self.uiHints().get('previewTag', 'previewFilePath')
            elementViewerWidget = ElementViewerWidget([], previewTag)

            # by default lets it fill the whole width
            width = self.uiHints().get('previewWidth', 0)
            if width:
                elementViewerWidget.setFixedWidth(width)

            height = self.uiHints().get('previewHeight', self.__defaultPreviewHeight)
            elementViewerWidget.setFixedHeight(height)
            if self.optionValue():
                previewElements = [self.optionValue()]
                # preview image sequence support
                if self.uiHints().get('previewSequence', False) and isinstance(self.optionValue(), ImageElement):
                    previewElements = self.optionValue().sequenceElements()
                elementViewerWidget.setElements(previewElements)
            mainLayout.addWidget(elementViewerWidget, 100)
        mainLayout.addWidget(self.__mainWidget)

        if not self.uiHints().get('displayValue', True):
            self.__mainWidget.setVisible(False)


OptionVisual.register('element', ElementOptionVisual)
OptionVisual.registerFallbackDefaultVisual('element', Element)
OptionVisual.registerExample('element', 'preview', None, {'preview': True, 'previewHeight': 180})
OptionVisual.registerExample('element', 'displayValue', None, {'displayValue': False})
OptionVisual.registerExample('element', 'previewSequence', None, {'preview': True, 'previewSequence': True, 'previewHeight': 180})
