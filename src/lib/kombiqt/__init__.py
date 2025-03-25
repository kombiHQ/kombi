import sys
from . import OptionVisual
from . import Widget
from . import Window
from . import Menu
from .App import App

def init():
    """
    Initialize the default kombi app.
    """
    app = App(sys.argv)
    window = Window.MainWindow.run(sys.argv)
    window.show()
    window.activateWindow()
    sys.exit(app.exec_())

def initScriptEditor():
    """
    Initialize the script editor app.
    """
    app = App(sys.argv)
    window = Window.ScriptEditorWindow(
        rootPath=sys.argv[1] if len(sys.argv) > 1 else ''
    )
    window.show()
    window.activateWindow()
    sys.exit(app.exec_())
