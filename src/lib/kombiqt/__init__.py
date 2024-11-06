import sys
from .App import App

def init():
    """
    Initialize the qt app.
    """
    app = App(sys.argv)
    sys.exit(app.exec_())
