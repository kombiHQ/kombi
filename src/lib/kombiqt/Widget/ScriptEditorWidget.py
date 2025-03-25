import os
import re
import weakref
import functools
import traceback
from kombi.Resource import Resource as kombiResource
from io import StringIO
from contextlib import redirect_stdout
from .CodeTextEditWidget import CodeTextEditWidget
from .PythonTextEditWidget import PythonTextEditWidget
from ..Resource import Resource

# making a copy of the globals at this point. This will be shared with the
# code execution
codeExecutionGlobals = dict(globals())  # noqa: E402

from Qt import QtCore, QtGui, QtWidgets

class ScriptEditorWidget(QtWidgets.QWidget):
    """
    Python script editor widget.
    """
    codeChanged = QtCore.Signal()
    openFilePath = QtCore.Signal(str, int)
    __codeChangedWaitTime = 1000

    def __init__(self, code='', filePath='', parent=None) -> None:
        """
        Initialize the ScriptEditorWidget.
        """
        super().__init__(parent)

        self.__buildWidget()

        # when loading the file path lets collapse the output widget
        # by default
        if filePath:
            self.setOutputDisplay(False)

        self.setFilePath(filePath)
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
            self.saveFile(ignoreCurrentFilePath=False)

        # Control+Z: undo
        elif event.modifiers() == QtCore.Qt.ControlModifier and event.key() == QtCore.Qt.Key_Z:
            self.__codeEditor.highlighter().highlightDocument(self.__codeEditor.textCursor(), force=True)

        # Control+R: redo
        elif event.modifiers() == QtCore.Qt.ControlModifier and event.key() == QtCore.Qt.Key_R:
            self.__codeEditor.redo()
            self.__codeEditor.highlighter().highlightDocument(self.__codeEditor.textCursor(), force=True)
            return

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

    def printHelp(self, additionalHelp=None):
        """
        Print the formatted help in the output widget.

        The additionalHelp argument allows you to pass a list of extra lines
        that will be included as part of the help content.
        """
        self.setOutputDisplay(True)

        self.__outputWidget.setTextColor(QtGui.QColor(130, 130, 130))
        self.__outputWidget.setFontWeight(QtGui.QFont.Normal)
        self.__outputWidget.append(kombiResource.asciiBanner())
        self.__outputWidget.append("Script Editor Shortcuts:")
        if additionalHelp:
            for line in additionalHelp:
                self.__outputWidget.append(line)
        self.__outputWidget.append("CTRL+Enter          Execute selected lines, or the entire script if none is selected.")
        self.__outputWidget.append("CTRL+SHIFT+Enter    Same as above but, profiling the execution and launching the profile when the execution is completed.")
        self.__outputWidget.append("CTRL+/              Comment or uncomment selected lines.")
        self.__outputWidget.append("CTRL+S              Save the current script.")
        self.__outputWidget.append("CTRL+F              Focus the \"Find\" field to search for text.")
        self.__outputWidget.append("CTRL+H              Open the \"Find and Replace\" field to search and replace text.")
        self.__outputWidget.append("CTRL+G              Go to specific line.")
        self.__outputWidget.append("CTRL+Z              Undo changes.")
        self.__outputWidget.append("CTRL+R              Redo changes.")
        self.__outputWidget.setTextColor(QtGui.QColor(171, 178, 191))

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
        self.__codeEditor = PythonTextEditWidget()
        self.__outputWidget = _OutputTextEdit()
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
        self.__outputWidget.openFilePath.connect(self.openFilePath.emit)

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
        self.__codeEditor.highlighter().highlightDocument(cursor, force=True)

        # resetting the undo stack
        self.__codeEditor.document().setUndoRedoEnabled(False)
        self.__codeEditor.document().setUndoRedoEnabled(True)

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

    def saveFile(self, ignoreCurrentFilePath=False):
        """
        Save the code to the file path.
        """
        if ignoreCurrentFilePath or not self.filePath():
            fileName, _ = QtWidgets.QFileDialog.getSaveFileName(
                self,
                'Save Script',
                self.filePath(),
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

    def gotoLine(self, line):
        """
        Go to specific line in the code.
        """
        self.__codeEditor.gotoLine(line)

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
            document = self.__codeEditor.document()
            cursor = document.find(
                self.__findWidget.text(),
                options=QtGui.QTextDocument.FindCaseSensitively
            )

            if cursor.isNull():
                return

            while not cursor.isNull():
                cursor.beginEditBlock()
                cursor.removeSelectedText()
                cursor.insertText(self.__replaceWidget.text())
                cursor.endEditBlock()

                # continue searching after the replaced text
                cursor = document.find(
                    self.__findWidget.text(),
                    options=QtGui.QTextDocument.FindCaseSensitively
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
        self.__codeEditor.highlighter().highlightDocument(self.__codeEditor.textCursor())
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


class _OutputTextEdit(CodeTextEditWidget):
    """
    Output text edit widget.
    """
    openFilePath = QtCore.Signal(str, int)
    __exceptionFilePathRegEx = r'^.*File "(.*\.[pP][yY])", line ([0-9]+)'

    def __init__(self, *args, **kwargs):
        """
        Create an _OutputTextEdit object.
        """
        super().__init__(showLineNumber=False, *args, **kwargs)
        self.setReadOnly(True)

        self.__pythonFileFormat = QtGui.QTextCharFormat()
        self.__pythonFileFormat.setBackground(QtGui.QColor(204, 151, 87))

    def contextMenuEvent(self, e):
        """
        Re-Implementation to grab the context menu and add script editor actions.
        """
        contextMenu = self.createStandardContextMenu()
        openFilePath = None
        openLine = 0

        # get selected text and check if that is a valid path
        selectedText = self.textCursor().selectedText().strip()
        if selectedText and os.path.exists(selectedText):
            openFilePath = selectedText

        # parse file path from exception
        if not openFilePath:
            cursorPosition = self.cursorForPosition(e.pos())
            lineNumber = cursorPosition.blockNumber()
            currentLine = cursorPosition.block().text()
            mouseCurrentChar = cursorPosition.position() - cursorPosition.block().position()
            for match in re.finditer(self.__exceptionFilePathRegEx, currentLine):
                filePath = match.group(1)
                lineNumber = match.group(2)
                if mouseCurrentChar >= match.start(1) and mouseCurrentChar <= match.end(1):
                    openFilePath = filePath
                    openLine = int(lineNumber)

        if openFilePath:
            openInScriptEditorAction = QtWidgets.QAction(
                'Open "{}" in script editor'.format(os.path.basename(openFilePath)),
                self
            )
            openInScriptEditorAction.triggered.connect(
                functools.partial(self.openFilePath.emit, openFilePath, openLine)
            )
            contextMenu.insertSeparator(contextMenu.actions()[0])
            contextMenu.insertAction(contextMenu.actions()[0], openInScriptEditorAction)
        contextMenu.exec_(e.globalPos())
