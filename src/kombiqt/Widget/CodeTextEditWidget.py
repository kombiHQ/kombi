from ..Resource import Resource
from Qt import QtCore, QtGui, QtWidgets

class CodeTextEditWidget(QtWidgets.QTextEdit):
    """
    A custom QTextEdit widget designed for displaying and editing code.
    """
    executeCode = QtCore.Signal(str)
    __lineAreaActiveLine = QtGui.QColor(131, 137, 150)
    __lineAreaInactiveLine = QtGui.QColor(91, 97, 110)
    __backgroundColor = QtGui.QColor(40, 44, 52)

    def __init__(self, showLineNumber=True, *args, **kwargs):
        """
        Create a CodeTextEditWidget object.
        """
        super().__init__(*args, *kwargs)

        self.setObjectName('codeEditor')
        self.setStyleSheet('font-size: {}px'.format(Resource.fontSize()))
        self.setAcceptRichText(False)
        self.setFocusPolicy(QtCore.Qt.StrongFocus)

        self.__showLineNumber = showLineNumber
        if showLineNumber:
            self.setWordWrapMode(QtGui.QTextOption.NoWrap)
            self.__lineNumberArea = _LineNumberAreaWidget(self)
            self.document().blockCountChanged.connect(self.__updateLineNumberArea)
            self.verticalScrollBar().valueChanged.connect(self.__updateLineNumberArea)
            self.cursorPositionChanged.connect(self.__updateLineNumberArea)

        # workaround necessary to show the blinking text cursor
        self.setPlainText('')

    def hasLineNumber(self):
        """
        Return a boolean telling if the line numbers are displayed.
        """
        return self.__showLineNumber

    def setPlainText(self, text):
        """
        Override the setPlainText to recalculate tabWidth on update.
        """
        super().setPlainText(text)
        self.__computeTabWidth()

    def setStyleSheet(self, styleSheet):
        """
        Override the stylesheet to recalculate tabWidth on update.
        """
        super().setStyleSheet(styleSheet)
        self.__computeTabWidth()

    def resizeEvent(self, event: QtGui.QResizeEvent):
        """
        Handle widget resize events.
        """
        super(CodeTextEditWidget, self).resizeEvent(event)
        if not self.hasLineNumber():
            return

        contentRect = self.contentsRect()
        self.__lineNumberArea.setGeometry(
            QtCore.QRect(
                contentRect.left(),
                contentRect.top(),
                self.__lineNumberAreaWidth(),
                contentRect.height()
            )
        )

    def lineNumberAreaPaintEvent(self, event: QtGui.QPaintEvent):
        """
        Paint the line numbers in the line number area.
        """
        self.verticalScrollBar().setSliderPosition(self.verticalScrollBar().sliderPosition())
        painter = QtGui.QPainter(self.__lineNumberArea)
        painter.setFont(self.font())
        painter.fillRect(event.rect(), self.__backgroundColor)

        blockNumber = self.__firstVisibleBlockId()
        block = self.document().findBlockByNumber(blockNumber)
        if blockNumber > 0:
            prevBlock = self.document().findBlockByNumber(blockNumber - 1)
        else:
            prevBlock = block

        if blockNumber > 0:
            translateY = -self.verticalScrollBar().sliderPosition()
        else:
            translateY = 0

        top = self.viewport().geometry().top()
        additionalMargin = 0
        if blockNumber:
            additionalMargin = self.document().documentLayout().blockBoundingRect(
                prevBlock
            ).translated(
                0,
                translateY
            ).intersected(
                self.viewport().geometry()
            ).height()
        top += additionalMargin
        bottom = top + int(self.document().documentLayout().blockBoundingRect(block).height())
        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                if self.textCursor().blockNumber() == blockNumber:
                    painter.setPen(self.__lineAreaActiveLine)
                else:
                    painter.setPen(self.__lineAreaInactiveLine)
                painter.drawText(
                    -5,
                    int(top),
                    self.__lineNumberArea.width(),
                    self.fontMetrics().height(),
                    QtCore.Qt.AlignRight,
                    str(blockNumber + 1)
                )
            block = block.next()
            top = bottom
            bottom = top + int(self.document().documentLayout().blockBoundingRect(block).height())
            blockNumber += 1

    def __lineNumberAreaWidth(self):
        """
        Calculate the width required for the line number area.
        """
        space = 20 + self.fontMetrics().horizontalAdvance(str(self.document().blockCount()))
        return space

    def __updateLineNumberArea(self):
        """
        Update the line number area.
        """
        self.verticalScrollBar().setSliderPosition(self.verticalScrollBar().sliderPosition())
        rect = self.contentsRect()
        self.__lineNumberArea.update(0, rect.y(), self.__lineNumberArea.width(), rect.height())
        self.setViewportMargins(self.__lineNumberAreaWidth(), 0, 0, 0)
        dy = self.verticalScrollBar().sliderPosition()
        if dy > -1:
            self.__lineNumberArea.scroll(0, dy)
        first_block_id = self.__firstVisibleBlockId()
        if first_block_id == 0 or self.textCursor().block().blockNumber() == first_block_id - 1:
            self.verticalScrollBar().setSliderPosition(dy - self.document().documentMargin())

    def __firstVisibleBlockId(self):
        """
        Get the ID of the first visible block in the document.
        """
        textCursor = QtGui.QTextCursor(self.document())
        textCursor.movePosition(QtGui.QTextCursor.Start)
        for i in range(self.document().blockCount()):
            block = textCursor.block()
            r1 = self.viewport().geometry()
            r2 = self.document().documentLayout().blockBoundingRect(block).translated(
                self.viewport().geometry().x(),
                self.viewport().geometry().y() - self.verticalScrollBar().sliderPosition()
            ).toRect()
            if r1.contains(r2, True):
                return i
            textCursor.movePosition(QtGui.QTextCursor.NextBlock)
        return 0

    def __computeTabWidth(self):
        """
        Compute the tab widget based on the current font size.
        """
        tabWidth = QtGui.QFontMetrics(self.font()).horizontalAdvance(' ')
        self.setTabStopDistance(tabWidth * 4)

class _LineNumberAreaWidget(QtWidgets.QWidget):
    """
    Custom widget to hold the area used to render the line numbers.

    This widget was initially based on this thread:
    https://stackoverflow.com/questions/2443358/how-to-add-lines-numbers-to-qtextedit
    """

    def __init__(self, editor):
        """
        Initialize the _LineNumberAreaWidget with a reference to the associated code editor.
        """
        super(_LineNumberAreaWidget, self).__init__(editor)
        self.__codeEditor = editor

    def sizeHint(self):
        """
        Return the preferred size of the line number area.
        """
        return QtCore.QSize(self.__codeEditor.__lineNumberAreaWidth(), 0)

    def paintEvent(self, event):
        """
        Delegate the painting event to the code editor.
        """
        self.__codeEditor.lineNumberAreaPaintEvent(event)
