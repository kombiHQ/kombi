from ...Task import Task
from ...Element import Element

class SequenceInfoTask(Task):
    """
    Task used to assign element variables about the sequence first, last and total frames.
    """

    def __init__(self, *args, **kwargs):
        """
        Create a sequence info task object.
        """
        super(SequenceInfoTask, self).__init__(*args, **kwargs)

        self.setOption('firstName', 'first')
        self.setOption('lastName', 'last')
        self.setOption('totalName', 'total')

    def _perform(self):
        """
        Implement the execution of the task.
        """
        result = []

        for elementGroup in Element.group(self.elements()):
            firstElement = elementGroup[0]
            lastElement = elementGroup[-1]

            for element in elementGroup:
                newElement = element.clone()
                newElement.setVar(
                    self.templateOption('firstName', element),
                    firstElement.var('frame')
                )
                newElement.setVar(
                    self.templateOption('lastName', element),
                    lastElement.var('frame')
                )
                newElement.setVar(
                    self.templateOption('totalName', element),
                    len(elementGroup)
                )
                result.append(newElement)

        return result


# registering task
Task.register(
    'sequenceInfo',
    SequenceInfoTask
)
