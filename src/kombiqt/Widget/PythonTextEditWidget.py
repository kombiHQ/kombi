import os
import re
import keyword
import builtins
from kombi.Task import Task
from kombi.Template import Template
from kombi.Element.Fs.FsElement import FsElement
from .CodeTextEditWidget import CodeTextEditWidget

try:
    import jedi
    hasJediSupport = True
except ImportError:
    hasJediSupport = False

try:
    import pycallgraph
except ImportError:
    hasPyCallGraph = False
else:
    hasPyCallGraph = True

from Qt import QtCore, QtGui, QtWidgets

class PythonTextEditWidget(CodeTextEditWidget):
    """
    A specialized CodeTextEditWidget for editing and displaying Python code.
    """
    __dotExecutable = os.environ.get(
        'KOMBI_GRAPHVIZ_DOT_EXECUTABLE',
        'dot'
    )

    def __init__(self, showLineNumber=True, parent=None):
        """
        Create a PythonTextEditWidget object.
        """
        super(PythonTextEditWidget, self).__init__(showLineNumber=showLineNumber, parent=parent)

        self.__completer = QtWidgets.QCompleter(self)
        self.__completer.setCaseSensitivity(QtCore.Qt.CaseInsensitive)
        self.__completer.setCompletionMode(QtWidgets.QCompleter.PopupCompletion)
        self.__completer.setWidget(self)
        self.__completer.activated.connect(self.__acceptSuggestion)

        self.__highlighter = _PythonSyntaxHighlighter(self.document())

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
        # Control+Enter: Execute code
        elif event.modifiers() & QtCore.Qt.ControlModifier and event.key() == QtCore.Qt.Key_Return:
            code = cursor.selectedText()
            if not code:
                code = self.toPlainText()

            # cleaning-up code before execution
            code = code.replace('\u2029', '\n')

            # when CTRL + SHIFT + ENTER is pressed profiling the execution
            if hasPyCallGraph and event.modifiers() & QtCore.Qt.ShiftModifier:
                profileOutputPng = Template('!kt (tmp)/kombi_profile_(rand).png').value()
                graphviz = pycallgraph.output.GraphvizOutput()
                graphviz.output_file = profileOutputPng
                graphviz.tool = self.__dotExecutable
                with pycallgraph.PyCallGraph(output=graphviz):
                    self.executeCode.emit(code)

                # launching profile
                if os.path.exists(profileOutputPng):
                    launchDefaultApplicationTask = Task.create('launchWithDefaultApplication')
                    launchDefaultApplicationTask.add(FsElement.createFromPath(profileOutputPng))
                    launchDefaultApplicationTask.output()
            # otherwise, only execute the code
            else:
                self.executeCode.emit(code)

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

            # if the current line is empty, containing only indentation,
            # we remove the indentation before adding a new indented line
            if len(currentLine.strip()) == 0:
                cursor.movePosition(QtGui.QTextCursor.StartOfBlock)
                cursor.movePosition(QtGui.QTextCursor.EndOfBlock, QtGui.QTextCursor.KeepAnchor)
                cursor.insertText('')

            cursor.insertBlock()
            cursor.insertText(' ' * indentation + ('    ' if currentLine and currentLine[-1] == ':' else ''))
            self.setTextCursor(cursor)
        # Backspace: Remove indentation if the line is empty
        elif event.key() == QtCore.Qt.Key_Backspace:
            # in case of a selection is in place we don't look for indentation
            if cursor.selectedText():
                super().keyPressEvent(event)
            else:
                currentPosition = cursor.positionInBlock()
                cursor.movePosition(QtGui.QTextCursor.StartOfBlock)
                currentLine = cursor.block().text()
                if currentLine[:currentPosition].strip() == "":
                    indentLength = len(currentLine[:currentPosition])
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
                position = cursor.position()
                cursor.movePosition(QtGui.QTextCursor.StartOfBlock)
                text = cursor.block().text()
                if text.startswith('    '):
                    cursor.movePosition(QtGui.QTextCursor.EndOfBlock, QtGui.QTextCursor.KeepAnchor)
                    cursor.insertText(text[4:])
                    cursor.setPosition(position - 4)
                    self.setTextCursor(cursor)

        # Default behavior for other keys
        else:
            super().keyPressEvent(event)

        if hasJediSupport and event.key() in (QtCore.Qt.Key_Return, QtCore.Qt.Key_ParenLeft, QtCore.Qt.Key_ParenRight, QtCore.Qt.Key_Space):
            self.__completer.popup().hide()

        elif hasJediSupport and event.key() == QtCore.Qt.Key_Period or self.__completer.popup().isVisible():
            self.__updateAutoComplete()

    def gotoLine(self, line):
        """
        Go to specific line in the code.
        """
        cursor = self.textCursor()
        cursor.movePosition(QtGui.QTextCursor.Start)

        for _ in range(int(line) - 1):
            cursor.movePosition(QtGui.QTextCursor.Down)

        self.setTextCursor(cursor)

        if line > 0:
            self.centerVerticalScroll()

    def centerVerticalScroll(self):
        """
        Center vertical scroll based on current line.
        """
        cursor = self.textCursor()
        blockNumber = cursor.blockNumber()

        blockHeight = self.document().documentLayout().blockBoundingRect(cursor.block()).height()
        totalHeight = self.viewport().height()

        scrollPosition = int(blockNumber * blockHeight - totalHeight / 2 + blockHeight / 2)
        self.verticalScrollBar().setValue(scrollPosition)

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

        # in case of numbers don't show auto-complete
        if currentLineText.split(' ')[-1].split('#')[-1].split(',')[-1].split('(')[-1].replace('.', '').isdigit():
            return

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
        self.__completer.popup().setFont(self.font())
        self.__completer.popup().setGeometry(cursorRect.x() + 30, cursorRect.y() + 10, 300, 150)
        self.__completer.popup().scrollToTop()

    def __acceptSuggestion(self, suggestion):
        """
        Insert the suggestion it into the editor at the current cursor position.
        """
        cursor = self.textCursor()
        textBeforeCursor = self.toPlainText()[:cursor.position()]
        currentLineText = textBeforeCursor.splitlines()[-1]
        cursor.movePosition(
            QtGui.QTextCursor.Left,
            QtGui.QTextCursor.KeepAnchor,
            len(currentLineText.split('.')[-1])
        )
        cursor.insertText(suggestion)

        # when the suggestion is a callable, lets move the cursor one char back
        if suggestion.endswith('()'):
            cursor.movePosition(QtGui.QTextCursor.Left, QtGui.QTextCursor.KeepAnchor, 1)
            cursor.clearSelection()
            self.setTextCursor(cursor)

class _PythonSyntaxHighlighter(QtGui.QSyntaxHighlighter):
    """
    Implement a basic python syntax highlighter.
    """
    __keywords = r"\b({})\b|^\s+(@)".format('|'.join(filter(lambda x: not hasattr(builtins, x), keyword.kwlist)))
    __builtins = r"((?<=^)|(?<=[^.]))\b({})\b".format('|'.join(dir(builtins)))
    __builtinExceptions = r"((?<=^)|(?<=[^.]))\b({})\b".format('|'.join(filter(lambda x: isinstance(getattr(builtins, x), type) and x and issubclass(getattr(builtins, x), BaseException), dir(builtins))))
    __comments = r"#.*?(?=#|$)"
    __lineContinuation = r"\\$"
    __numeric = r"\b[0-9]*\b"
    __decorators = r"(?<=@)[A-Za-z_][A-Za-z0-9_]*\b[\s]*?"
    __strings = r"(['\"])(?:(?!\1|\\).|\\.)*?\1"
    __functions = r"\b(?<=def)\s+[A-Za-z_][A-Za-z0-9_]*\b[\s]*?(?=\()"
    __classes = r"\b(?<=class)\s+[A-Za-z_][A-Za-z0-9_]*\b[\s]*?(?=:|\()"
    __docstrings = r'"""([\s\S]*?)"""|\'\'\'([\s\S]*?)\'\'\''
    __docstringsEnclosure = r'(""")|(\'\'\')'
    __trailingWhitespaces = r'\s+$'
    __tabs = r'\t'

    def __init__(self, parent=None):
        """
        Create ab _PythonSyntaxHighlighter object.
        """
        super().__init__(parent)
        self.__defaultTextFormat = QtGui.QTextCharFormat()

        self.__numericFormat = QtGui.QTextCharFormat()
        self.__numericFormat.setForeground(QtGui.QColor(204, 151, 87))

        self.__keywordFormat = QtGui.QTextCharFormat()
        self.__keywordFormat.setForeground(QtGui.QColor(198, 120, 221))
        self.__keywordFormat.setFontWeight(QtGui.QFont.Bold)

        self.__commentFormat = QtGui.QTextCharFormat()
        self.__commentFormat.setForeground(QtGui.QColor(91, 97, 110))

        self.__stringFormat = QtGui.QTextCharFormat()
        self.__stringFormat.setForeground(QtGui.QColor(137, 192, 114))

        self.__builtinExceptionsFormat = QtGui.QTextCharFormat()
        self.__builtinExceptionsFormat.setForeground(QtGui.QColor(229, 192, 123))

        self.__functionFormat = QtGui.QTextCharFormat()
        self.__functionFormat.setForeground(QtGui.QColor(97, 175, 238))

        self.__trailingWhitespaceFormat = QtGui.QTextCharFormat()
        self.__trailingWhitespaceFormat.setBackground(QtGui.QColor(38, 50, 71))

        self.__tabFormat = QtGui.QTextCharFormat()
        self.__tabFormat.setBackground(QtGui.QColor(71, 38, 59))

        self.__documentDocstrings = []
        self.__documentDocstringsHash = ''

    def highlightBlock(self, text):
        """
        Compute the highlighting for the input text block.
        """
        # processing highlight for current block
        self.__highlightRanges = []
        self.__applyHighlight(self.__numeric, text, self.__numericFormat)
        self.__applyHighlight(self.__keywords, text, self.__keywordFormat)
        self.__applyHighlight(self.__builtins, text, self.__functionFormat)
        self.__applyHighlight(self.__lineContinuation, text, self.__functionFormat)
        self.__applyHighlight(self.__builtinExceptions, text, self.__builtinExceptionsFormat)
        self.__applyHighlight(self.__functions, text, self.__functionFormat)
        self.__applyHighlight(self.__classes, text, self.__functionFormat)
        self.__applyHighlight(self.__decorators, text, self.__functionFormat)
        self.__applyHighlight(self.__strings, text, self.__stringFormat)
        self.__applyHighlight(self.__docstringsEnclosure, text, self.__stringFormat)
        self.__applyHighlight(self.__comments, text, self.__commentFormat, checkRanges=True)
        self.__applyHighlight(self.__trailingWhitespaces, text, self.__trailingWhitespaceFormat)
        self.__applyHighlight(self.__tabs, text, self.__tabFormat)

    def highlightDocument(self, cursor, force=False):
        """
        Compute the highlights for the document, especially when the highlight spans multiple lines.
        """
        self.__documentDocstrings = []

        # highlighting multi-line docstrings
        currentSignature = ''
        text = self.document().toPlainText()
        for match in re.finditer(self.__docstrings, text):
            start = match.start()
            end = match.end()
            line = text[max(text[:start].rfind('\n'), 0): start]
            currentSignature += str(end - start) + '-' + line + ','
            self.__documentDocstrings.append([start, end])

        newHash = hash(currentSignature)
        if force or self.__documentDocstringsHash != newHash:
            self.__documentDocstringsHash = newHash
            cursor.beginEditBlock()
            currentPosition = cursor.position()

            # resetting all highlight before proceeding
            cursor.select(QtGui.QTextCursor.Document)
            cursor.setCharFormat(self.__defaultTextFormat)

            # applying doctstring highlight
            for start, end in self.__documentDocstrings:
                cursor.setPosition(start + 2)
                cursor.setPosition(end - 3, QtGui.QTextCursor.KeepAnchor)
                cursor.setCharFormat(self.__stringFormat)
            cursor.setPosition(currentPosition)
            cursor.endEditBlock()

    def __applyHighlight(self, pattern, text, textFormat, checkRanges=False, *args):
        """
        Apply the syntax highlighting using the provided regular expression pattern.
        """
        currentBlockPosition = self.currentBlock().position()
        for match in re.finditer(pattern, text, *args):
            skip = False
            start, end = match.span()

            # ignoring any highlight inside of doc strings (computed
            # separately)
            for docstringStart, docstringEnd in self.__documentDocstrings:
                if currentBlockPosition + start > docstringStart and currentBlockPosition + end < docstringEnd:
                    skip = True
                    break

            if not skip and checkRanges:
                # ignoring previous highlighted
                for ignoreStart, ignoreEnd in self.__highlightRanges:
                    if start > ignoreStart and start < ignoreEnd:
                        self.__highlightRanges.append([start, end])
                        skip = True
                        break

            if skip:
                continue
            self.__highlightRanges.append([start, end])

            # apply to the whole line
            if checkRanges:
                self.setFormat(start, len(text), textFormat)
            else:
                self.setFormat(start, end - start, textFormat)
