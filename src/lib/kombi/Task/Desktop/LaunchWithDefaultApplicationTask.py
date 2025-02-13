import os
import pathlib
import platform
import subprocess
from ..Task import Task

class LaunchWithDefaultApplicationTask(Task):
    """
    Open the file with the default desktop application.
    """

    def __init__(self, *args, **kwargs):
        """
        Create a LaunchWithDefaultApplicationTask object.
        """
        super(LaunchWithDefaultApplicationTask, self).__init__(*args, **kwargs)

        self.setMetadata(
            'match.types',
            [
                'file'
            ]
        )

        self.setMetadata('ui.task.showExecutionSettings', False)
        self.setMetadata('ui.task.showInContextMenu', True)
        self.setMetadata('ui.task.menuIcon', 'icons/openWithDefaultApplication.png')

    def _perform(self):
        """
        Implement the execution of the task.
        """
        result = []
        for element in self.elements():
            result.append(self.__processElement(element))

        return result

    def __processElement(self, element):
        """
        Process individually each element.
        """
        filePath = pathlib.Path(element.var('fullPath'))
        system = platform.system().lower()

        # Windows
        if system == 'windows':
            os.startfile(filePath)
        # macOS
        elif system == "darwin":
            subprocess.run(["open", filePath])
        # Linux
        else:
            subprocess.run(["xdg-open", filePath])

        return element


# registering task
Task.register('launchWithDefaultApplication', LaunchWithDefaultApplicationTask)
