from ...Task import Task
from ...Element import Element

class SliceSequenceTask(Task):
    """
    Implements a task that slices the image sequence elements.
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

        for elementGroup in Element.group(self.elements()):
            sliceBegin = int(self.templateOption('sliceTotalAtBegin', elementGroup[0]))
            sliceEnd = int(self.templateOption('sliceTotalAtEnd', elementGroup[-1]))

            slicedElements = elementGroup[sliceBegin:]
            if sliceEnd:
                slicedElements = slicedElements[:-sliceEnd]
            result += slicedElements

        return result


# registering task
Task.register(
    'sliceSequence',
    SliceSequenceTask
)
