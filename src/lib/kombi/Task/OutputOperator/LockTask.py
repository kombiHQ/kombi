import os
from kombi.Task import Task


class LockTask(Task):
    """
    Implements a task that creates a lock file.
    """

    def __init__(self, *args, **kwargs):
        """
        Create a touch with info object.
        """
        super(LockTask, self).__init__(*args, **kwargs)
        self.setOption("assignLockToContextVar", 'lock')

        self.setMetadata('dispatch.split', False)
        self.setMetadata('dispatch.splitSize', 1)

    def _perform(self):
        """
        Implement the execution of the task.
        """
        infoCrates = self.infoCrates()

        result = []
        alreadyCreated = set()
        for infoCrate in infoCrates:
            targetFilePath = self.target(infoCrate)

            if targetFilePath not in alreadyCreated:
                try:
                    os.makedirs(
                        os.path.dirname(targetFilePath)
                    )
                except Exception:
                    pass

                # touching the file
                with open(targetFilePath, 'a'):
                    os.utime(targetFilePath)

                alreadyCreated.add(targetFilePath)

            newInfoCrate = infoCrate.clone()
            newInfoCrate.setVar(
                self.templateOption('assignLockToContextVar', infoCrate),
                targetFilePath,
                True
            )
            result.append(newInfoCrate)

        return result


# registering task
Task.register(
    'lock',
    LockTask
)
