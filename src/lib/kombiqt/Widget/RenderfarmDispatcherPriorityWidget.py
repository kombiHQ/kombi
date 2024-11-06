import os
from Qt import QtWidgets


class RenderfarmDispatcherPriorityWidget(QtWidgets.QComboBox):
    """
    Display a list of priorities that can be used to override the overall priority.
    """

    priorityPreset = os.environ.get('KOMBIUI_DISPATCHER_RENDERFARM_PRIORITY_PRESET', 'High Priority=95,Low Priority=10')

    def __init__(self, *args, **kwargs):
        """
        Create a widget object.
        """
        super(RenderfarmDispatcherPriorityWidget, self).__init__(*args, **kwargs)
        self.__buildPriorityPreset()

    def selectPriorityName(self, priority):
        """
        Load the default priority.
        """
        for index in range(self.count()):
            value = str(self.itemText(index)).lower()
            if value == priority.lower():
                self.setCurrentIndex(index)
                break

    def selectedPriorityValue(self):
        """
        Return the name of the current selected priority.
        """
        return self.currentData()

    def selectedPriorityName(self):
        """
        Return the name of the current selected priority.
        """
        return str(self.currentText())

    def __buildPriorityPreset(self):
        """
        Create a drop down menu with the priorities.
        """
        self.addItem('Default Priority', 0)

        priorities = self.priorityPreset.split(',')
        for priority in priorities:
            if not priority:
                continue

            priorityParts = priority.split('=')
            self.addItem(
                priorityParts[0],
                int(priorityParts[-1]) if priorityParts[-1].isdigit() else priorityParts[-1]
            )
