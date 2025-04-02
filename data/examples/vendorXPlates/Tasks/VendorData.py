import json
import os
from kombi.Element.Fs.FsElement import FsElement
from kombi.Task import Task

class VendorData(Task):
    """
    Implements a task that writes a json file.
    """

    def __init__(self, *args, **kwargs):
        """
        Create a VendorData object.
        """
        super().__init__(*args, **kwargs)

        self.setOption(
            'elementArray',
            FsElement.createFromPath(
                os.path.dirname(os.path.abspath(__file__))
            ).children()
        )

    def _perform(self):
        """
        Implement the execution of the task.
        """
        element = self.elements()[0]
        targetFilePath = self.target(element)

        data = {
            "vendorVersion": element.var('vendorVersion'),
            "plateName": element.var('plateName')
        }

        with open(targetFilePath, 'w') as f:
            json.dump(data, f)

        return super(VendorData, self)._perform()


# registering task
Task.register(
    'vendorData',
    VendorData
)
