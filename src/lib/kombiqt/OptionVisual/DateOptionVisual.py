from Qt import QtWidgets, QtCore
from .OptionVisual import OptionVisual


class DateOptionVisual(OptionVisual):
    """
    Implement the widget for a date option.
    """

    def __init__(self, optionValue, uiHints=None):
        """
        Create DateOptionVisual object.
        """
        super().__init__(optionValue, uiHints)

        self.__buildWidget()

    def __buildWidget(self):
        """
        Implement the widget.
        """
        mainLayout = QtWidgets.QVBoxLayout()
        mainLayout.setContentsMargins(2, 2, 2, 2)
        self.setLayout(mainLayout)

        self.__mainWidget = QtWidgets.QLineEdit(str(self.optionValue()))
        self.__mainWidget.textEdited.connect(self.__onValueChanged)
        self.__mainWidget.setMaximumWidth(self.uiHints().get('width', 100))
        self.__calendarWidget = _CalendarWidget()
        self.__calendarWidget.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        self.__calendarWidget.resize(self.__calendarWidget.minimumSizeHint())

        self.__calendarWidget.setGridVisible(False)
        self.__calendarWidget.setFirstDayOfWeek(QtCore.Qt.Monday)
        self.__calendarWidget.setVerticalHeaderFormat(QtWidgets.QCalendarWidget.NoVerticalHeader)
        self.__calendarWidget.clicked.connect(self.__onCalendarChanged)

        mainLayout.addWidget(self.__calendarWidget)
        mainLayout.addWidget(self.__mainWidget)

        self.__updateCalendar()

    def __onCalendarChanged(self, date):
        """
        Triggered when the calendar is clicked.
        """
        self.__mainWidget.setText(date.toString("yyyy-MM-dd"))
        self.__onValueChanged()

    def __updateCalendar(self):
        """
        Update the calendar wiget information.
        """
        currentDate = QtCore.QDate.fromString(self.__mainWidget.text(), "yyyy-M-d")
        if currentDate.isValid():
            self.__calendarWidget.setSelectedDate(currentDate)

    def __onValueChanged(self):
        """
        Triggered when the text field is changed.
        """
        value = self.__mainWidget.text()
        self.__updateCalendar()
        self.valueChanged.emit(value)


class _CalendarWidget(QtWidgets.QCalendarWidget):
    """
    Internal calendar implementation necessary to disable the scrolling wheel.
    """

    def __init__(self) -> None:
        """
        Create a CalendarWidget object.
        """
        super().__init__()

        # disabling scrolling wheel for all calendar children...
        for view in self.findChildren(QtWidgets.QWidget):
            view.installEventFilter(self)

    def eventFilter(self, obj, event):
        """
        Allow all events except from scrolling wheel.
        """
        if event.type() == QtCore.QEvent.Wheel:
            event.ignore()
            return True
        return False


# registering option visual
OptionVisual.register('date', DateOptionVisual)

# registering examples
OptionVisual.registerExample('date', 'default', '1950-01-22')
