from ...Task import Task
from ...InfoCrate import InfoCrate

class RenumberSequenceTask(Task):
    """
    Implements a task that renumbers the frame variable in image sequence infoCrates.

    This task returns a new infoCrate with the renumbered frame assigned to
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

        for infoCrateGroup in InfoCrate.group(self.infoCrates()):
            for index, infoCrate in enumerate(infoCrateGroup):
                newFrame = self.option('startAt') + index

                # cloning the infoCrate before modifying it
                newInfoCrate = infoCrate.clone()

                # setting original frame as infoCrate variable
                newInfoCrate.setVar(self.option('originalFrameVarName'), infoCrate.var('frame'))
                newInfoCrate.setVar(self.option('renumberedFrameVarName'), newFrame)
                result.append(newInfoCrate)

        return result


# registering task
Task.register(
    'renumberSequence',
    RenumberSequenceTask
)
