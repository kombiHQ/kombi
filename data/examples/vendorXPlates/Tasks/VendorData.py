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
        crawler = self.crawlers()[0]
        targetFilePath = self.target(crawler)

        data = {
            "vendorVersion": crawler.var('vendorVersion'),
            "plateName": crawler.var('plateName')
        }

        with open(targetFilePath, 'w') as f:
            json.dump(data, f)

        return super(VendorData, self)._perform()


# registering task
Task.register(
    'vendorData',
    VendorData
)
