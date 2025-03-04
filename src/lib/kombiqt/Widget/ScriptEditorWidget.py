import os
import re
import weakref
import functools
import traceback
from io import StringIO
from contextlib import redirect_stdout
from ..Resource import Resource

try:
    import jedi
    hasJediSupport = True
except ImportError:
    hasJediSupport = False

# making a copy of the globals at this point. This will be shared with the
# code execution
codeExecutionGlobals = dict(globals())  # noqa: E402

from Qt import QtCore, QtGui, QtWidgets

class ScriptEditorWidget(QtWidgets.QWidget):
    """
    Python script editor widget.
    """
    codeChanged = QtCore.Signal()
    __codeChangedWaitTime = 2500

    def __init__(self, code='', filePath='', parent=None) -> None:
        """
        Initialize the ScriptEditorWidget.
        """
        super().__init__(parent)

        self.__buildWidget()
        self.setFilePath(filePath)

        # when loading the file path lets collapse the output widget
        # by default
        if filePath:
            self.setOutputDisplay(False)

        if code:
            self.setCode(code)
        self.__buildConnections()

        # for performance optimization, code changes are
        # only computed after the user stops typing
        self.__codeChangedTimer = QtCore.QTimer()
        self.__codeChangedTimer.setSingleShot(True)
        self.__codeChangedTimer.timeout.connect(self.__emitCodeChangedSignal)

    def keyPressEvent(self, event):
        """
        Handle the hotkeys available for the script editor.
        """
        # Control+- or Control+=: control the font zoom
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

        # Control+0: reset font zoom
        elif event.modifiers() == QtCore.Qt.ControlModifier and event.key() == QtCore.Qt.Key_0:
            size = Resource.fontSize()
            self.__outputWidget.setStyleSheet(f"font-size: {size}px")
            self.__codeEditor.setStyleSheet(f"font-size: {size}px")

        # Control+S: save
        elif event.modifiers() == QtCore.Qt.ControlModifier and event.key() == QtCore.Qt.Key_S:
            self.saveFile()

        # Control+F: find text
        elif event.modifiers() == QtCore.Qt.ControlModifier and event.key() == QtCore.Qt.Key_F:
            self.__findWidget.selectAll()
            self.__findWidget.setFocus()

        # Control+H: find/replace text
        elif event.modifiers() == QtCore.Qt.ControlModifier and event.key() == QtCore.Qt.Key_H:
            self.__setReplaceDisplay(True)
            self.__findWidget.selectAll()
            self.__findWidget.setFocus()

        # Escape: reset the focus back to the code editor
        elif event.key() == QtCore.Qt.Key_Escape and self.__findWidget.hasFocus():
            self.__setReplaceDisplay(False)

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
        self.__verticalSplitter = QtWidgets.QSplitter(QtCore.Qt.Vertical)
        self.__mainLayout = QtWidgets.QVBoxLayout()
        self.__mainLayout.setContentsMargins(4, 4, 4, 2)
        self.__mainLayout.setSpacing(0)
        self.__codeEditor = _CodeEditorWidget()
        self.__codeEditor.setWordWrapMode(QtGui.QTextOption.NoWrap)
        self.__codeEditor.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.__outputWidget = QtWidgets.QTextEdit()
        self.__outputWidget.setObjectName('codeEditor')
        self.__outputWidget.setAcceptRichText(False)
        self.__outputWidget.setReadOnly(True)
        self.__outputWidget.setFocusPolicy(QtCore.Qt.ClickFocus)
        self.__mainLayout.addWidget(self.__verticalSplitter, 10)

        self.__verticalSplitter.addWidget(self.__outputWidget)
        self.__verticalSplitter.addWidget(self.__codeEditor)
        self.setLayout(self.__mainLayout)
        self.__textCursorPositionLabel = QtWidgets.QLabel('')
        self.__textCursorPositionLabel.setObjectName('textCursorPositionLabel')
        self.__textCursorPositionLabel.setAlignment(QtCore.Qt.AlignRight)

        self.__findWidget = QtWidgets.QLineEdit()
        self.__findWidget.setObjectName('findText')
        self.__findWidget.setPlaceholderText('Find (press Enter to cycle through matches)')

        self.__replaceWidget = QtWidgets.QLineEdit()
        self.__replaceWidget.setObjectName('findText')
        self.__replaceWidget.setPlaceholderText('Replace')
        self.__replaceAll = QtWidgets.QPushButton('Replace All')
        self.__replaceCancel = QtWidgets.QPushButton('Cancel')

        statusLayout = QtWidgets.QHBoxLayout()
        statusLayout.addWidget(self.__findWidget)
        statusLayout.addWidget(self.__replaceWidget)
        statusLayout.addWidget(self.__replaceAll)
        statusLayout.addSpacing(5)
        statusLayout.addWidget(self.__replaceCancel)
        statusLayout.addStretch()
        statusLayout.addWidget(self.__textCursorPositionLabel)
        self.__setReplaceDisplay(False)
        self.__mainLayout.addLayout(statusLayout, 0)
        self.__searchLastPost = 0

    def __buildConnections(self):
        """
        Build all the base widget connections.
        """
        self.__codeEditor.textChanged.connect(self.__onCodeEditorChanged)
        self.__codeEditor.executeCode.connect(self.executeCode)
        self.__codeEditor.cursorPositionChanged.connect(self.__onUpdateStatus)

        self.__findWidget.textEdited.connect(functools.partial(self.__onFindTextEdit, False))
        self.__findWidget.returnPressed.connect(functools.partial(self.__onFindTextEdit, True))

        self.__replaceCancel.pressed.connect(functools.partial(self.__setReplaceDisplay, False))
        self.__replaceAll.pressed.connect(self.__onReplaceAll)

    def setOutputDisplay(self, display):
        """
        Control the display of output widget.
        """
        if display:
            if not self.outputDisplay():
                self.__verticalSplitter.setSizes((50, 50))
        else:
            self.__verticalSplitter.setSizes((0, 100))

    def outputDisplay(self):
        """
        Return if the output widget is being displayed.
        """
        return self.__verticalSplitter.sizes()[0] > 0

    def executeCode(self, code):
        """
        Execute the code using exec() and capture any output.
        """
        # making sure the code is saved before execution
        self.__emitCodeChangedSignal()

        f = StringIO()
        failed = False
        self.__outputWidget.append(code)
        self.setOutputDisplay(True)

        mainWindow = self
        while mainWindow.parent():
            mainWindow = mainWindow.parent()

        if mainWindow:
            codeExecutionGlobals['mainWindow'] = weakref.ref(mainWindow)

        with redirect_stdout(f):
            try:
               try:
                    # using eval() to evaluate the code and print the result. This is helpful
                    # for debugging by allowing you to inspect the result of expressions
                    # line by line without needing to insert additional print statements.
                    # Note that eval() is limited in functionality and will likely raise 
                    # a SyntaxError if used with non-expression code. However, it works well
                    # for evaluating simple expressions or function calls.
                    print(eval(code, codeExecutionGlobals))
                except SyntaxError:
                    # if eval() raises a SyntaxError, fallback to using exec().
                    # Unlike eval(), exec() executes entire code and does not return
                    # a result, making it suitable for more complex statements or scripts.
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

        cursor = self.__codeEditor.textCursor()
        cursor.movePosition(QtGui.QTextCursor.EndOfBlock)
        self.__codeEditor.setTextCursor(cursor)
        self.__codeEditor.highlighter().highlightDocument()

    def setFilePath(self, filePath, loadCode=True):
        """
        Associate a file path with the script editor.

        When defined the code will be serialized using the file path when changed.
        """
        self.__filePath = filePath

        if filePath and loadCode:
            if not os.path.exists(filePath):
                return

            self.loadFile()

    def filePath(self):
        """
        Return the file associated with the file path with the script editor.
        """
        return self.__filePath

    def saveFile(self):
        """
        Save the code to the file path.
        """
        if not self.filePath():
            fileName, _ = QtWidgets.QFileDialog.getSaveFileName(
                self,
                'Save Script',
                '',
                'Python Files (*.py);;All Files (*)'
            )

            # cancelled
            if not fileName:
                return

            self.setFilePath(fileName, loadCode=False)

        with open(self.filePath(), 'w') as f:
            f.write(self.code())

        self.__emitCodeChangedSignal()

    def isModified(self):
        """
        Return a boolean telling if the code is different from the original contents of the file path.
        """
        assert self.filePath(), "File path not defined!"

        if not os.path.exists(self.filePath()):
            return True

        with open(self.filePath()) as f:
            return hash(f.read()) != hash(self.code())

    def loadFile(self):
        """
        Load the code from the file path.
        """
        assert self.filePath(), "File path not defined!"

        with open(self.filePath()) as f:
            self.setCode(f.read())

    def output(self):
        """
        Get the current output from the output widget.
        """
        return self.__outputWidget.toPlainText()

    def codeEditorWidget(self):
        """
        Return the code editor widget.
        """
        return self.__codeEditor

    def outputWidget(self):
        """
        Return the output widget.
        """
        return self.__outputWidget

    def clearOutput(self):
        """
        Clear the output widget.
        """
        self.__outputWidget.clear()

    def __onReplaceAll(self):
        """
        Triggered when replace all button is pressed.
        """
        reply = QtWidgets.QMessageBox.question(
            self,
            "Replace all",
            "Are you sure you want to replace all?",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
            QtWidgets.QMessageBox.No
        )

        if reply == QtWidgets.QMessageBox.Yes:
            self.__codeEditor.setPlainText(
                self.__codeEditor.toPlainText().replace(
                    self.__findWidget.text(),
                    self.__replaceWidget.text()
                )
            )

    def __setReplaceDisplay(self, display):
        """
        Set the display of the replace widget.
        """
        self.__replaceWidget.setVisible(display)
        self.__replaceAll.setVisible(display)
        self.__replaceCancel.setVisible(display)

        if not display:
            self.__codeEditor.setFocus()

    def __onFindTextEdit(self, moveCursor, text=''):
        """
        Triggered when the find field has changed.
        """
        # clearing any existing selection before starting the search
        text = self.__findWidget.text()
        cursor = self.__codeEditor.textCursor()
        cursor.clearSelection()
        self.__codeEditor.setTextCursor(cursor)

        # in case the find text is ":<digits>" we actually move to the line (like vim)
        if text.startswith(':') and text[1:].isdigit():
            self.__codeEditor.gotoLine(int(text[1:]))
            return

        if not text:
            self.__searchLastPost = 0
            return

        content = self.__codeEditor.toPlainText()
        postion = content.find(text, self.__searchLastPost if moveCursor else 0)

        #  looping back to the begin
        if postion == -1:
            postion = content.find(text)

        # moving text cursor and selecting text
        if postion != -1:
            cursor.setPosition(postion)
            cursor.movePosition(QtGui.QTextCursor.Right, QtGui.QTextCursor.KeepAnchor, len(text))
            self.__codeEditor.setTextCursor(cursor)
            self.__searchLastPost = postion + len(text)

    def __onCodeEditorChanged(self):
        """
        Update the script editor configuration when the code changes.
        """
        self.__codeChangedTimer.stop()
        self.__codeChangedTimer.start(self.__codeChangedWaitTime)

    def __emitCodeChangedSignal(self):
        """
        Emit the code changed signal.
        """
        # in case there is a pending timer
        self.__codeEditor.highlighter().highlightDocument()
        if self.__codeChangedTimer.isActive():
            self.__codeChangedTimer.stop()

        self.codeChanged.emit()

    def __onUpdateStatus(self):
        """
        Triggered when text cursor is changed to update the status bar.
        """
        cursor = self.__codeEditor.textCursor()
        line = cursor.blockNumber() + 1
        column = cursor.columnNumber() + 1

        # Update the status bar text
        self.__textCursorPositionLabel.setText(f"Line: {line}, Column: {column} ")

    def __del__(self):
        """
        Stop any running timer before the object is deleted.
        """
        try:
            if self.__codeChangedTimer.isActive():
                self.__codeChangedTimer.stop()
                self.codeChanged.emit()
        # We intentionally ignore any runtime errors that may occur at this point, as
        # they could be caused by the internal C++ object already being deleted. For example:
        # RuntimeError: Internal C++ object (self.__codeChangedTimer) has already been deleted.
        except RuntimeError:
            pass


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
        self.setStyleSheet('font-size: {}px'.format(Resource.fontSize()))

        self.__lineNumberArea = _LineNumberAreaWidget(self)

        self.document().blockCountChanged.connect(self.updateLineNumberArea)
        self.verticalScrollBar().valueChanged.connect(self.updateLineNumberArea)
        self.cursorPositionChanged.connect(self.updateLineNumberArea)
        self.setAcceptRichText(False)

        self.__completer = QtWidgets.QCompleter(self)
        self.__completer.setCaseSensitivity(QtCore.Qt.CaseInsensitive)
        self.__completer.setCompletionMode(QtWidgets.QCompleter.PopupCompletion)
        self.__completer.setWidget(self)
        self.__completer.activated.connect(self.__acceptSuggestion)

        self.__highlighter = _PythonSyntaxHighlighter(self.document())

        # workaround necessary to show the blinking text cursor
        self.setPlainText('')

    def highlighter(self):
        """
        Return the syntax highlight associated with the document.
        """
        return self.__highlighter

    def keyPressEvent(self, event):
        """
        Handle key press events for custom behavior.
        """
        cursor = self.textCursor()

        if self.__completer.popup().isVisible() and self.__completer.popup().currentIndex().isValid() and event.key() == QtCore.Qt.Key_Return:
            self.__acceptSuggestion(self.__completer.popup().currentIndex().data())

        # Control+G: Change the current line
        elif event.modifiers() == QtCore.Qt.ControlModifier and event.key() == QtCore.Qt.Key_G:
            self.__gotoLinePopup()
        # Control+Enter: Execute selected code
        elif event.modifiers() == QtCore.Qt.ControlModifier and event.key() == QtCore.Qt.Key_Return:
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

        if hasJediSupport and event.key() in (QtCore.Qt.Key_Return, QtCore.Qt.Key_ParenLeft, QtCore.Qt.Key_ParenRight, QtCore.Qt.Key_Space):
            self.__completer.popup().hide()

        elif hasJediSupport and event.key() == QtCore.Qt.Key_Period or self.__completer.popup().isVisible():
            self.__updateAutoComplete()

    def lineNumberAreaWidth(self):
        """
        Calculate the width required for the line number area.
        """
        space = 20 + self.fontMetrics().horizontalAdvance(str(self.document().blockCount()))
        return space

    def updateLineNumberArea(self):
        """
        Update the line number area.
        """
        self.verticalScrollBar().setSliderPosition(self.verticalScrollBar().sliderPosition())
        rect = self.contentsRect()
        self.__lineNumberArea.update(0, rect.y(), self.__lineNumberArea.width(), rect.height())
        self.setViewportMargins(self.lineNumberAreaWidth(), 0, 0, 0)
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
        painter.setFont(self.font())
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
        additionalMargin = 0
        if blockNumber:
            additionalMargin = self.document().documentLayout().blockBoundingRect(prevBlock).translated(0, translateY).intersected(self.viewport().geometry()).height()
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

    def gotoLine(self, line):
        """
        Go to specific line in the code.
        """
        cursor = self.textCursor()
        cursor.movePosition(QtGui.QTextCursor.Start)

        for _ in range(int(line) - 1):
            cursor.movePosition(QtGui.QTextCursor.Down)

        self.setTextCursor(cursor)

    def __gotoLinePopup(self):
        """
        Display a popup to change the line.
        """
        line, ok = QtWidgets.QInputDialog.getText(
            self,
            "Script Editor",
            "Goto line:",
            text=''
        )
        if ok and line.isdigit():
            self.gotoLine(line)

    def __updateAutoComplete(self):
        """
        Update the auto-completion suggestions.

        Uses the Jedi library to query for suggestions and displays them in a popup.
        """
        cursor = self.textCursor()
        textBeforeCursor = self.toPlainText()[:cursor.position()]
        currentLineText = textBeforeCursor.splitlines()[-1]

        if not len(currentLineText.strip()):
            self.__completer.popup().hide()
            return

        # query jedi for auto complete suggestions
        try:
            completions = jedi.Script(self.toPlainText()).complete(
                len(textBeforeCursor.split('\n')),
                len(currentLineText)
            )
        except Exception:
            pass
        else:
            suggestions = []
            for completion in completions:
                if completion.type == 'function':
                    suggestions.append(completion.name + '()')
                else:
                    suggestions.append(completion.name)
            self.__displaySuggestions(suggestions)

    def __displaySuggestions(self, suggestions):
        """
        Display the given list of suggestions in the auto-completion popup.
        """
        if not suggestions:
            return
        self.__model = QtCore.QStringListModel(suggestions, self.__completer)
        self.__completer.setModel(self.__model)
        self.__completer.setCompletionPrefix('')

        cursorRect = self.mapToGlobal(self.cursorRect().bottomRight())

        self.__completer.complete()
        self.__completer.popup().setGeometry(cursorRect.x() + 30, cursorRect.y() + 10, 300, 150)
        self.__completer.popup().scrollToTop()

    def __acceptSuggestion(self, suggestion):
        """
        Insert the suggestion it into the editor at the current cursor position.
        """
        cursor = self.textCursor()
        textBeforeCursor = self.toPlainText()[:cursor.position()]
        currentLineText = textBeforeCursor.splitlines()[-1]
        cursor.insertText(suggestion[len(currentLineText.split('.')[-1]):])

        # when the suggestion is a callable, lets move the cursor one char back
        if suggestion.endswith('()'):
            cursor.movePosition(QtGui.QTextCursor.Left, QtGui.QTextCursor.KeepAnchor, 1)
            cursor.clearSelection()
            self.setTextCursor(cursor)

class _PythonSyntaxHighlighter(QtGui.QSyntaxHighlighter):
    """
    Implement a basic python syntax highlighter.
    """
    __keywords = r"\b(def|class|as|in|not|and|or|if|else|elif|for|while|try|except|finally|with|import|from|return|yield|pass|break|continue|del|global|lambda|assert|raise|True|False|None)\b"
    __comments = r"#.*"
    __numeric = r"[0-9]"
    __decorators = r"^\s*@.*$"
    __strings = r"\"[^\"]*\"|\'[^\']*\'"
    __functions = r"\b[A-Za-z_][A-Za-z0-9_]*\b(?=\()"
    __docstrings = r'"""([\s\S]*?)"""|\'\'\'([\s\S]*?)\'\'\''

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
        self.__applyHighlight(self.__decorators, text, self.__functionFormat)
        self.__applyHighlight(self.__strings, text, self.__stringFormat)
        self.__applyHighlight(self.__comments, text, self.__commentFormat)

    def highlightDocument(self):
        """
        Compute the highlights for the document, especially when the highlight spans multiple lines.
        """
        cursor = QtGui.QTextCursor(self.document())
        cursor.beginEditBlock()

        for match in re.finditer(self.__docstrings, self.document().toPlainText()):
            start = match.start()
            end = match.end()

            cursor.setPosition(start)
            cursor.setPosition(end, QtGui.QTextCursor.KeepAnchor)
            cursor.setCharFormat(self.__stringFormat)

        cursor.endEditBlock()

    def __applyHighlight(self, pattern, text, textFormat, *args):
        """
        Apply the syntax highlighting using the provided regular expression pattern.
        """
        for match in re.finditer(pattern, text, *args):
            start, end = match.span()
            self.setFormat(start, end - start, textFormat)
