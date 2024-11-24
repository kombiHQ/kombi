from ...Task import Task
from ...InfoCrate import InfoCrate

class SliceSequenceTask(Task):
    """
    Implements a task that slices the image sequence infoCrates.
    """

    def __init__(self, *args, **kwargs):
        """
        Create a slice sequence task.
        """
        super(SliceSequenceTask, self).__init__(*args, **kwargs)

        self.setOption('sliceTotalAtBegin', 0)
        self.setOption('sliceTotalAtEnd', 0)

    def _perform(self):
        """
        Implement the execution of the task.
        """
        result = []

        for infoCrateGroup in InfoCrate.group(self.infoCrates()):
            sliceBegin = int(self.templateOption('sliceTotalAtBegin', infoCrateGroup[0]))
            sliceEnd = int(self.templateOption('sliceTotalAtEnd', infoCrateGroup[-1]))

            slicedInfoCrates = infoCrateGroup[sliceBegin:]
            if sliceEnd:
                slicedInfoCrates = slicedInfoCrates[:-sliceEnd]
            result += slicedInfoCrates

        return result


# registering task
Task.register(
    'sliceSequence',
    SliceSequenceTask
)
