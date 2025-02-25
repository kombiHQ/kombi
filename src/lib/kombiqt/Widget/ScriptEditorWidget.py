import re
import weakref
from io import StringIO
from contextlib import redirect_stdout
import traceback

# making a copy of the globals at this point. This will be shared with the
# code execution
codeExecutionGlobals = dict(globals())  # noqa: E402

from Qt import QtCore, QtGui, QtWidgets

class ScriptEditorWidget(QtWidgets.QWidget):
    """
    Python script editor widget.
    """
    codeChanged = QtCore.Signal()

    def __init__(self, parent=None) -> None:
        """
        Initialize the ScriptEditorWidget.
        """
        super().__init__(parent)
        self.__buildWidget()

    def keyPressEvent(self, event):
        """
        Control the script editor font size by detecting ctr + = and ctrl + -.
        """
        if event.modifiers() == QtCore.Qt.ControlModifier and event.key() in (QtCore.Qt.Key_Equal, QtCore.Qt.Key_Minus):
            currentFont = self.__outputWidget.font()
            size = currentFont.pixelSize()

            if event.key() == QtCore.Qt.Key_Equal:
                size += 1
            elif event.key() == QtCore.Qt.Key_Minus:
                size -= 1

            if size < 1:
                size = 1

            currentFont.setPixelSize(size)
            self.__outputWidget.setStyleSheet(f"font-size: {size}px")
            self.__codeEditor.setStyleSheet(f"font-size: {size}px")

        super().keyPressEvent(event)

    def wheelEvent(self, event):
        """
        Control the script editor font size.
        """
        if event.modifiers() == QtCore.Qt.ControlModifier:
            currentFont = self.__outputWidget.font()
            currentSize = currentFont.pixelSize()

            # zoom in or out depending on the direction of the scroll wheel
            newSize = None
            if event.angleDelta().y() > 0:
                newSize = currentSize + 1
            elif currentSize > 1:
                newSize = currentSize - 1

            if newSize is not None:
                currentFont.setPixelSize(newSize)
                self.__outputWidget.setStyleSheet(f"font-size: {newSize}px")
                self.__codeEditor.setStyleSheet(f"font-size: {newSize}px")

        super().wheelEvent(event)

    def __buildWidget(self):
        """
        Build the base widgets.
        """
        self.__splitter = QtWidgets.QSplitter(QtCore.Qt.Vertical)
        self.__mainLayout = QtWidgets.QVBoxLayout()
        self.__mainLayout.setContentsMargins(0, 0, 0, 0)
        self.__mainLayout.setSpacing(0)
        self.__codeEditor = _CodeEditorWidget()
        self.__codeEditor.setWordWrapMode(QtGui.QTextOption.NoWrap)
        self.__codeEditor.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.__codeEditor.textChanged.connect(self.__onCodeEditorChanged)
        self.__outputWidget = QtWidgets.QTextEdit()
        self.__outputWidget.setObjectName('codeEditor')
        self.__outputWidget.setAcceptRichText(False)
        self.__outputWidget.setReadOnly(True)
        self.__outputWidget.setFocusPolicy(QtCore.Qt.ClickFocus)
        self.__mainLayout.addWidget(self.__splitter)
        self.__splitter.addWidget(self.__outputWidget)
        self.__splitter.addWidget(self.__codeEditor)
        self.setLayout(self.__mainLayout)
        self.__codeEditor.executeCode.connect(self.executeCode)
        self.__statusBar = QtWidgets.QLabel('')
        self.__statusBar.setObjectName('scriptEditorStatus')
        self.__statusBar.setAlignment(QtCore.Qt.AlignRight)
        self.__mainLayout.addWidget(self.__statusBar)
        self.__codeEditor.cursorPositionChanged.connect(self.__onUpdateStatus)

    def executeCode(self, code):
        """
        Execute the code using exec() and capture any output.
        """
        f = StringIO()
        failed = False
        self.__outputWidget.append(code)

        mainWindow = self
        while mainWindow.parent():
            mainWindow = mainWindow.parent()

        if mainWindow:
            codeExecutionGlobals['mainWindow'] = weakref.ref(mainWindow)

        with redirect_stdout(f):
            try:
                exec(code, codeExecutionGlobals)
            except Exception:
                failed = True
                errorLines = traceback.format_exc().splitlines()
                del errorLines[1:3]
                print('\n'.join(errorLines))

        if failed:
            self.__outputWidget.setFontWeight(QtGui.QFont.Bold)
            self.__outputWidget.setTextColor(QtGui.QColor(224, 108, 117))
        else:
            self.__outputWidget.setTextColor(QtGui.QColor(220, 220, 220))
        self.__outputWidget.append(f.getvalue())
        self.__outputWidget.setFontWeight(QtGui.QFont.Normal)
        self.__outputWidget.setTextColor(QtGui.QColor(171, 178, 191))

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
        self.codeChanged.emit()

    def __onUpdateStatus(self):
        """
        Triggered when text cursor is changed to update the status bar.
        """
        cursor = self.__codeEditor.textCursor()
        line = cursor.blockNumber() + 1
        column = cursor.columnNumber() + 1

        # Update the status bar text
        self.__statusBar.setText(f"Line: {line}, Column: {column} ")

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
    __lineAreaActiveLine = QtGui.QColor(131, 137, 150)
    __lineAreaInactiveLine = QtGui.QColor(91, 97, 110)
    __backgroundColor = QtGui.QColor(40, 44, 52)

    def __init__(self, parent=None):
        """
        Initialize the CodeEditorWidget and set up the line number area.
        """
        super(_CodeEditorWidget, self).__init__(parent)
        self.setObjectName('codeEditor')
        self.__lineNumberArea = _LineNumberAreaWidget(self)

        self.document().blockCountChanged.connect(self.updateLineNumberAreaWidth)
        self.verticalScrollBar().valueChanged.connect(self.updateLineNumberArea)
        self.textChanged.connect(self.updateLineNumberArea)
        self.cursorPositionChanged.connect(self.updateLineNumberArea)
        self.setAcceptRichText(False)  # Only accept plain text

        _PythonSyntaxHighlighter(self.document())

        self.updateLineNumberAreaWidth(0)  # Initialize the line number area width

    def keyPressEvent(self, event):
        """
        Handle key press events for custom behavior.
        """
        cursor = self.textCursor()

        # Control+Enter: Execute selected code
        if event.modifiers() == QtCore.Qt.ControlModifier and event.key() == QtCore.Qt.Key_Return:
            code = cursor.selectedText()
            if not code:
                code = self.toPlainText()
            self.executeCode.emit(code.replace('\u2029', '\n'))
        # Control+/: Replace the selected text with the new commented/uncommented code
        elif event.modifiers() == QtCore.Qt.ControlModifier and event.key() == QtCore.Qt.Key_Slash:
            lines = cursor.selectedText().splitlines()

            # Check if the lines are already commented
            newLines = []
            if list(filter(lambda x: x.strip().startswith('#'), lines)):
                for line in lines:
                    processedLine = line.lstrip('#').lstrip()
                    if len(line) != processedLine:
                        newLines.append(line.replace("#", '', 1))
                    else:
                        newLines.append(line)
            # Comment the selected lines
            else:
                newLines = map(lambda x: '#' + x, lines)
            cursor.insertText('\n'.join(newLines))
        # Enter: Insert a new line with proper indentation
        elif event.key() == QtCore.Qt.Key_Return and self.textCursor().block().length() - 1 == self.textCursor().positionInBlock():
            cursor.movePosition(QtGui.QTextCursor.EndOfBlock)
            currentLine = cursor.block().text()
            indentation = len(currentLine) - len(currentLine.lstrip())
            cursor.insertBlock()
            cursor.insertText(' ' * indentation + ('    ' if currentLine and currentLine[-1] == ':' else ''))
            self.setTextCursor(cursor)
        # Backspace: Remove indentation if the line is empty
        elif event.key() == QtCore.Qt.Key_Backspace:
            cursor.movePosition(QtGui.QTextCursor.StartOfBlock)
            currentLine = cursor.block().text()
            if currentLine.strip() == "":
                indentLength = len(currentLine)
                if indentLength >= 4:
                    cursor.movePosition(QtGui.QTextCursor.StartOfBlock)
                    cursor.movePosition(QtGui.QTextCursor.Right, QtGui.QTextCursor.KeepAnchor, 4)
                    cursor.removeSelectedText()
                else:
                    super().keyPressEvent(event)
            else:
                super().keyPressEvent(event)
        # Tab: Insert 4 spaces
        elif event.key() == QtCore.Qt.Key_Tab:
            selectedText = cursor.selectedText()
            selectionStart = cursor.selectionStart()
            if selectedText:
                # Split the selected text into lines
                lines = selectedText.splitlines()
                newLines = []
                for line in lines:
                    newLines.append('    ' + line)  # Keep the line as it is

                # Replace the selected text with the new lines
                cursor.insertText('\n'.join(newLines))

                # Select the newly inserted lines
                cursor.setPosition(selectionStart)  # Start of the selection
                cursor.setPosition(selectionStart + len('\n'.join(newLines)), QtGui.QTextCursor.KeepAnchor)  # End of the selection
                self.setTextCursor(cursor)
            else:
                cursor.insertText('    ')
                self.setTextCursor(cursor)
        # Shift+Tab: Remove 4 spaces if they exist at the start of the line
        elif event.key() == QtCore.Qt.Key_Backtab:
            selectedText = cursor.selectedText()
            selectionStart = cursor.selectionStart()
            if selectedText:
                # Split the selected text into lines
                lines = selectedText.splitlines()
                newLines = []
                for line in lines:
                    totalSpaces = len(line) - len(line.lstrip())
                    if line.startswith(' '):
                        newLines.append(line[4 if totalSpaces >= 4 else totalSpaces:])
                    else:
                        newLines.append(line)

                # Replace the selected text with the new lines
                cursor.insertText('\n'.join(newLines))

                # Select the newly inserted lines
                cursor.setPosition(selectionStart)  # Start of the selection
                cursor.setPosition(selectionStart + len('\n'.join(newLines)), QtGui.QTextCursor.KeepAnchor)  # End of the selection
                self.setTextCursor(cursor)
            else:
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
        painter.fillRect(event.rect(), self.__backgroundColor)
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

class _PythonSyntaxHighlighter(QtGui.QSyntaxHighlighter):
    """
    Implement a basic python syntax highlighter.
    """
    __keywords = r"\b(def|class|as|in|not|and|or|if|else|elif|for|while|try|except|finally|with|import|from|return|yield|pass|break|continue|del|global|lambda|assert|raise|True|False|None)\b"
    __comments = r"#.*"
    __numeric = r"[0-9]"
    __strings = r"\"[^\"]*\"|\'[^\']*\'"
    __functions = r"\b[A-Za-z_][A-Za-z0-9_]*\b(?=\()"

    def __init__(self, parent=None):
        """
        Create ab _PythonSyntaxHighlighter object.
        """
        super().__init__(parent)

        self.__numericFormat = QtGui.QTextCharFormat()
        self.__numericFormat.setForeground(QtGui.QColor(204, 151, 87))

        self.__keywordFormat = QtGui.QTextCharFormat()
        self.__keywordFormat.setForeground(QtGui.QColor(198, 120, 221))
        self.__keywordFormat.setFontWeight(QtGui.QFont.Bold)

        self.__commentFormat = QtGui.QTextCharFormat()
        self.__commentFormat.setForeground(QtGui.QColor(91, 97, 110))

        self.__stringFormat = QtGui.QTextCharFormat()
        self.__stringFormat.setForeground(QtGui.QColor(137, 192, 114))

        self.__functionFormat = QtGui.QTextCharFormat()
        self.__functionFormat.setForeground(QtGui.QColor(97, 175, 238))

    def highlightBlock(self, text):
        """
        Compute the highlighting for the input text block.
        """
        self.__applyHighlight(self.__numeric, text, self.__numericFormat)
        self.__applyHighlight(self.__keywords, text, self.__keywordFormat)
        self.__applyHighlight(self.__functions, text, self.__functionFormat)
        self.__applyHighlight(self.__strings, text, self.__stringFormat)
        self.__applyHighlight(self.__comments, text, self.__commentFormat)

    def __applyHighlight(self, pattern, text, text_format):
        """
        Apply the syntax highlighting using the provided regular expression pattern.
        """
        for match in re.finditer(pattern, text):
            start, end = match.span()
            self.setFormat(start, end - start, text_format)
