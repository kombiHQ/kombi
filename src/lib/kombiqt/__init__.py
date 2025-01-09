import sys
from . import OptionVisual
from . import Element
from . import Widget
from . import Window
from .App import App

def init():
    """
    Initialize the qt app.
    """
    app = App(sys.argv)
    sys.exit(app.exec_())
