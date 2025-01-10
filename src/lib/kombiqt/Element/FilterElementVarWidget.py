from kombi.Template import Template
from collections import OrderedDict
from Qt import QtCore, QtWidgets

class FilterElementVarWidget(QtWidgets.QWidget):
    """
    Filter element var widget.
    """

    filterChangedSignal = QtCore.Signal()

    def __init__(self):
        """
        Create an filter element var widget.
        """
        super(FilterElementVarWidget, self).__init__()

        self.__filterVarName = ""
        self.__ignoreFilterChangedSignal = False

        self.__currentCheckBoxes = OrderedDict()

        self.__mainLayout = QtWidgets.QVBoxLayout()
        self.__mainLayout.setSpacing(0)

        self.__buttonsLayout = QtWidgets.QHBoxLayout()
        self.__buttonsLayout.setSpacing(5)
        self.__buttonsLayout.addStretch()
        self.__mainLayout.addLayout(self.__buttonsLayout, 0)

        scrollArea = QtWidgets.QScrollArea()
        holderWidget = QtWidgets.QWidget()
        scrollArea.setWidget(holderWidget)
        scrollArea.setWidgetResizable(True)
        self.__contentLayout = QtWidgets.QVBoxLayout()
        self.__contentLayout.setSpacing(0)
        holderWidget.setLayout(self.__contentLayout)

        self.__mainLayout.addWidget(scrollArea, 1)

        self.setLayout(self.__mainLayout)

    def refresh(self, filterVarName, elements):
        """
        Refresh the widget contents.
        """
        self.__filterVarName = filterVarName

        varValues = set()
        for element in elements:
            if self.__filterVarName not in element.varNames():
                continue
            varValues.add(element.var(self.__filterVarName))

        # creating check box list
        newCheckBoxes = OrderedDict()
        for varName in sorted(varValues):
            widget = QtWidgets.QPushButton(Template.runProcedure('camelcasetospaced', str(varName)).capitalize())
            widget.setObjectName('filterElementVar')
            widget.setCheckable(True)
            widget.setChecked(self.__currentCheckBoxes[varName].isChecked() if varName in self.__currentCheckBoxes else False)
            widget.clicked.connect(self.__onStateChanged)

            newCheckBoxes[varName] = widget

        # clearing layout
        while self.__contentLayout.count():
            child = self.__contentLayout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        # adding check box list
        self.__currentCheckBoxes = newCheckBoxes
        for widget in self.__currentCheckBoxes.values():
            self.__contentLayout.addWidget(widget)
        self.__contentLayout.addStretch()

    def filterVarName(self):
        """
        Return the name of the element var name used to collect the filters.
        """
        return self.__filterVarName

    def checkedFilterVarValues(self):
        """
        Return a list of checked names for the current var name.
        """
        result = []
        for varValue, checkBox in self.__currentCheckBoxes.items():
            if checkBox.isChecked():
                result.append(varValue)

        if not result:
            result = list(self.__currentCheckBoxes.keys())

        return result

    def __onStateChanged(self, state=None):
        """
        Callback called when a check box state changes.
        """
        if self.__ignoreFilterChangedSignal:
            return

        # emitting the filter changed signal
        self.filterChangedSignal.emit()
