from io import StringIO
from contextlib import redirect_stdout
from Qt import QtCore, QtGui, QtWidgets
import traceback
from ..Resource import Resource
from kombi.Config import Config

class ScriptEditorWidget(QtWidgets.QWidget):
    __fontName = 'JetBrains Mono'

    def __init__(self, parent=None) -> None:
        """
        Initialize the ScriptEditorWidget.
        """
        super().__init__(parent)

        self.__buildWidget()

        # load any previous saved session
        self.__scriptEditorConfig = Config('scriptEditor')
        if self.__scriptEditorConfig.hasKey('code'):
            self.setCode(self.__scriptEditorConfig.value('code'))

    def wheelEvent(self, event):
        """
        Control the script editor font size.
        """
        if event.modifiers() == QtCore.Qt.ControlModifier:
            currentFont = self.__outputWidget.font()
            currentSize = currentFont.pointSize()

            # zoom in or out depending on the direction of the scroll wheel
            newSize = None
            if event.angleDelta().y() > 0:
                newSize = currentSize + 1
            elif currentSize > 1:
                newSize = currentSize - 1

            if newSize is not None:
                currentFont.setPointSize(newSize)
                self.__outputWidget.setFont(currentFont)
                self.__codeEditor.setFont(currentFont)

        super().wheelEvent(event)

    def __buildWidget(self):
        """
        Build the base widgets.
        """
        fontFound = False
        database = QtGui.QFontDatabase()
        for family in database.families():
            if family == self.__fontName:
                fontFound = True

        if not fontFound:
            Resource.loadFonts()
        font = QtGui.QFont(self.__fontName)
        font.setFixedPitch(True)
        font.setStyleHint(QtGui.QFont.TypeWriter)

        self.__splitter = QtWidgets.QSplitter(QtCore.Qt.Vertical)  # Splitter to separate code editor and output
        self.__mainLayout = QtWidgets.QVBoxLayout()  # Main layout
        self.__mainLayout.setContentsMargins(0, 0, 0, 0)
        self.__codeEditor = _CodeEditorWidget()  # Code editor widget
        self.__codeEditor.setWordWrapMode(QtGui.QTextOption.NoWrap)
        self.__codeEditor.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.__codeEditor.setFont(font)
        self.__codeEditor.textChanged.connect(self.__onCodeEditorChanged)
        self.__outputWidget = QtWidgets.QTextEdit()  # Output widget
        self.__outputWidget.setAcceptRichText(False)
        self.__outputWidget.setFont(font)
        self.__outputWidget.setReadOnly(True)
        self.__outputWidget.setFocusPolicy(QtCore.Qt.ClickFocus)
        self.__mainLayout.addWidget(self.__splitter)
        self.__splitter.addWidget(self.__outputWidget)
        self.__splitter.addWidget(self.__codeEditor)
        self.setLayout(self.__mainLayout)
        self.__codeEditor.executeCode.connect(self.executeCode)

    def executeCode(self, code):
        """
        Execute the code using exec() and capture any output.
        """
        f = StringIO()
        with redirect_stdout(f):
            print(code)
            try:
                compiledCode = compile(code, 'script editor', 'exec')
                exec(compiledCode, globals())
            except Exception:
                print('Error:')
                print('\n'.join(traceback.format_exc().splitlines()[3:]))
        self.__outputWidget.append(f.getvalue())

    def code(self):
        """
        Get the current code from the code editor.
        """
        return self.__codeEditor.toPlainText()

    def setCode(self, code):
        """
        Set the code in the code editor.
        """
        self.__codeEditor.setPlainText(code)

    def output(self):
        """
        Get the current output from the output widget.
        """
        return self.__outputWidget.toPlainText()

    def clearOutput(self):
        """
        Clear the output widget.
        """
        self.__outputWidget.clear()

    def __onCodeEditorChanged(self):
        """
        Update the script editor configuration when the code changes.
        """
        self.__scriptEditorConfig.setValue('code', self.__codeEditor.toPlainText())

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
        return QtCore.QSize(self.__codeEditor.lineNumberAreaWidth(), 0)

    def paintEvent(self, event):
        """
        Delegate the painting event to the code editor.
        """
        self.__codeEditor.lineNumberAreaPaintEvent(event)

class _CodeEditorWidget(QtWidgets.QTextEdit):
    """
    Simple code editor widget.

    This widget was initially based on this thread:
    https://stackoverflow.com/questions/2443358/how-to-add-lines-numbers-to-qtextedit
    """

    executeCode = QtCore.Signal(str)
    __lineAreaActiveLine = QtGui.QColor(120, 120, 120)
    __lineAreaInactiveLine = QtGui.QColor(50, 50, 50)

    def __init__(self, parent=None):
        """
        Initialize the CodeEditorWidget and set up the line number area.
        """
        super(_CodeEditorWidget, self).__init__(parent)
        self.__lineNumberArea = _LineNumberAreaWidget(self)

        self.document().blockCountChanged.connect(self.updateLineNumberAreaWidth)
        self.verticalScrollBar().valueChanged.connect(self.updateLineNumberArea)
        self.textChanged.connect(self.updateLineNumberArea)
        self.cursorPositionChanged.connect(self.updateLineNumberArea)
        self.setAcceptRichText(False)  # Only accept plain text

        self.updateLineNumberAreaWidth(0)  # Initialize the line number area width

    def keyPressEvent(self, event):
        """
        Handle key press events for custom behavior.
        """
        # Control+Enter: Execute selected code
        if event.modifiers() == QtCore.Qt.ControlModifier and event.key() == QtCore.Qt.Key_Return:
            cursor = self.textCursor()
            selectedText = cursor.selectedText().replace('\u2029', '\n')
            if selectedText:
                self.executeCode.emit(selectedText)
        # Enter: Insert a new line with proper indentation
        elif event.key() == QtCore.Qt.Key_Return:
            cursor = self.textCursor()
            cursor.movePosition(QtGui.QTextCursor.EndOfBlock)
            current_line = cursor.block().text()
            indentation = len(current_line) - len(current_line.lstrip())
            cursor.insertBlock()
            cursor.insertText(' ' * indentation + ('    ' if current_line and current_line[-1] == ':' else ''))
            self.setTextCursor(cursor)
        # Backspace: Remove indentation if the line is empty
        elif event.key() == QtCore.Qt.Key_Backspace:
            cursor = self.textCursor()
            cursor.movePosition(QtGui.QTextCursor.StartOfBlock)
            current_line = cursor.block().text()
            if current_line.strip() == "":
                indent_length = len(current_line)
                if indent_length >= 4:
                    cursor.movePosition(QtGui.QTextCursor.StartOfBlock)
                    cursor.movePosition(QtGui.QTextCursor.Right, QtGui.QTextCursor.KeepAnchor, 4)
                    cursor.removeSelectedText()
                else:
                    super().keyPressEvent(event)
            else:
                super().keyPressEvent(event)
        # Tab: Insert 4 spaces
        elif event.key() == QtCore.Qt.Key_Tab:
            cursor = self.textCursor()
            cursor.insertText('    ')
            self.setTextCursor(cursor)
        # Shift+Tab: Remove 4 spaces if they exist at the start of the line
        elif event.key() == QtCore.Qt.Key_Backtab:
            cursor = self.textCursor()
            cursor.movePosition(QtGui.QTextCursor.StartOfBlock)
            text = cursor.block().text()
            if text.startswith('    '):
                cursor.movePosition(QtGui.QTextCursor.EndOfBlock, QtGui.QTextCursor.KeepAnchor)
                cursor.insertText(text[4:])
                self.setTextCursor(cursor)
        # Default behavior for other keys
        else:
            super().keyPressEvent(event)

    def lineNumberAreaWidth(self):
        """
        Calculate the width required for the line number area.
        """
        digits = 1
        m = max(1, self.document().blockCount())
        while m >= 10:
            m /= 10
            digits += 1
        space = 13 + self.fontMetrics().horizontalAdvance('9') * digits
        return space

    def updateLineNumberAreaWidth(self, _):
        """
        Update the width of the line number area.
        """
        self.setViewportMargins(self.lineNumberAreaWidth(), 0, 0, 0)

    def updateLineNumberArea(self):
        """
        Update the line number area.
        """
        self.verticalScrollBar().setSliderPosition(self.verticalScrollBar().sliderPosition())
        rect = self.contentsRect()
        self.__lineNumberArea.update(0, rect.y(), self.__lineNumberArea.width(), rect.height())
        self.updateLineNumberAreaWidth(0)
        dy = self.verticalScrollBar().sliderPosition()
        if dy > -1:
            self.__lineNumberArea.scroll(0, dy)
        first_block_id = self.firstVisibleBlockId()
        if first_block_id == 0 or self.textCursor().block().blockNumber() == first_block_id - 1:
            self.verticalScrollBar().setSliderPosition(dy - self.document().documentMargin())

    def resizeEvent(self, event: QtGui.QResizeEvent):
        """
        Handle widget resize events.
        """
        super(_CodeEditorWidget, self).resizeEvent(event)
        contentRect = self.contentsRect()
        self.__lineNumberArea.setGeometry(QtCore.QRect(contentRect.left(), contentRect.top(), self.lineNumberAreaWidth(), contentRect.height()))

    def firstVisibleBlockId(self):
        """
        Get the ID of the first visible block in the document.
        """
        textCursor = QtGui.QTextCursor(self.document())
        textCursor.movePosition(QtGui.QTextCursor.Start)
        for i in range(self.document().blockCount()):
            block = textCursor.block()
            r1 = self.viewport().geometry()
            r2 = self.document().documentLayout().blockBoundingRect(block).translated(
                self.viewport().geometry().x(), self.viewport().geometry().y() - self.verticalScrollBar().sliderPosition()).toRect()
            if r1.contains(r2, True):
                return i
            textCursor.movePosition(QtGui.QTextCursor.NextBlock)
        return 0

    def lineNumberAreaPaintEvent(self, event: QtGui.QPaintEvent):
        """
        Paint the line numbers in the line number area.
        """
        self.verticalScrollBar().setSliderPosition(self.verticalScrollBar().sliderPosition())
        painter = QtGui.QPainter(self.__lineNumberArea)
        painter.fillRect(event.rect(), QtCore.Qt.lightGray)
        blockNumber = self.firstVisibleBlockId()
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
        if blockNumber == 0:
            additionalMargin = self.document().documentMargin() - 1 - self.verticalScrollBar().sliderPosition()
        else:
            additionalMargin = self.document().documentLayout().blockBoundingRect(prevBlock).translated(0, translateY).intersected(self.viewport().geometry()).height()
        top += additionalMargin
        bottom = top + int(self.document().documentLayout().blockBoundingRect(block).height())
        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                if self.textCursor().blockNumber() == blockNumber:
                    painter.setPen(self.__lineAreaActiveLine)
                else:
                    painter.setPen(self.__lineAreaInactiveLine)
                painter.drawText(-5, top, self.__lineNumberArea.width(), self.fontMetrics().height(), QtCore.Qt.AlignRight, str(blockNumber + 1))
            block = block.next()
            top = bottom
            bottom = top + int(self.document().documentLayout().blockBoundingRect(block).height())
            blockNumber += 1
