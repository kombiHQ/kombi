from ...Task import Task
from ...InfoCrate import InfoCrate

class SequenceInfoTask(Task):
    """
    Task used to assign infoCrate variables about the sequence first, last and total frames.
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

        for infoCrateGroup in InfoCrate.group(self.infoCrates()):
            firstInfoCrate = infoCrateGroup[0]
            lastInfoCrate = infoCrateGroup[-1]

            for infoCrate in infoCrateGroup:
                newInfoCrate = infoCrate.clone()
                newInfoCrate.setVar(
                    self.templateOption('firstName', infoCrate),
                    firstInfoCrate.var('frame')
                )
                newInfoCrate.setVar(
                    self.templateOption('lastName', infoCrate),
                    lastInfoCrate.var('frame')
                )
                newInfoCrate.setVar(
                    self.templateOption('totalName', infoCrate),
                    len(infoCrateGroup)
                )
                result.append(newInfoCrate)

        return result


# registering task
Task.register(
    'sequenceInfo',
    SequenceInfoTask
)
