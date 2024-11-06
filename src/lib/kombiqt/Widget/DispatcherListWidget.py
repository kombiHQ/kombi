import os
from kombi.TaskHolder.Dispatcher import Dispatcher
from Qt import QtWidgets


class DispatcherListWidget(QtWidgets.QComboBox):
    """
    Display the available dispatchers.
    """

    __defaultDispatcher = os.environ.get('KOMBI_DISPATCHER_DEFAULT', 'local').lower()

    def __init__(self, *args, **kwargs):
        """
        Create a dispatcher object.
        """
        super(DispatcherListWidget, self).__init__(*args, **kwargs)

        self.__loadDispatchers()
        self.selectDispatcher(self.__defaultDispatcher)

    def selectDispatcher(self, dispatcherName):
        """
        Load the default dispatcher.
        """
        for index in range(self.count()):
            value = str(self.itemText(index)).lower()
            if value == dispatcherName.lower():
                self.setCurrentIndex(index)
                break

    def selectedDispatcher(self):
        """
        Return the name of the current selected dispatcher.
        """
        return str(self.currentText())

    def __loadDispatchers(self):
        """
        Load the available dispatchers to the widget.
        """
        for dispatcherName in sorted(Dispatcher.registeredNames()):
            self.addItem(dispatcherName)
