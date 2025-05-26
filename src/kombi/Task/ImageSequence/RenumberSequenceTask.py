from ...Task import Task
from ...Element import Element

class RenumberSequenceTask(Task):
    """
    Implements a task that renumbers the frame variable in image sequence elements.

    This task returns a new element with the renumbered frame assigned to
    the "frame" variable (it can be changed through the option renumberedFrameVarName).
    The original frame is assigned to "originalFrame" variable (it can be changed through
    the option originalFrameVarName).
    """

    __startAtDefault = 1001

    def __init__(self, *args, **kwargs):
        """
        Create a renumber sequence task.
        """
        super(RenumberSequenceTask, self).__init__(*args, **kwargs)
        self.setOption('startAt', self.__startAtDefault)
        self.setOption('originalFrameVarName', 'originalFrame')
        self.setOption('renumberedFrameVarName', 'frame')

    def _perform(self):
        """
        Implement the execution of the task.
        """
        result = []

        for elementGroup in Element.group(self.elements()):
            for index, element in enumerate(elementGroup):
                newFrame = self.option('startAt') + index

                # cloning the element before modifying it
                newElement = element.clone()

                # setting original frame as element variable
                newElement.setVar(self.option('originalFrameVarName'), element.var('frame'))
                newElement.setVar(self.option('renumberedFrameVarName'), newFrame)
                result.append(newElement)

        return result


# registering task
Task.register(
    'renumberSequence',
    RenumberSequenceTask
)
