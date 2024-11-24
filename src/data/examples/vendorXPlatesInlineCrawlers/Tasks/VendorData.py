import json
from kombi.Task import Task

class VendorData(Task):
    """
    Implements a task that writes a json file.
    """

    def _perform(self):
        """
        Implement the execution of the task.
        """
        infoCrate = self.infoCrates()[0]
        targetFilePath = self.target(infoCrate)

        data = {
            "vendorVersion": infoCrate.var('vendorVersion'),
            "plateName": infoCrate.var('plateName')
        }

        with open(targetFilePath, 'w') as f:
            json.dump(data, f)

        return super(VendorData, self)._perform()


# registering task
Task.register(
    'vendorData',
    VendorData
)
