import os
from ..Task import Task

class ChownTask(Task):
    """
    Chown task that can be operated over a single file or over a directory path recursively.

    Require options: user, group
    """

    def __init__(self, *args, **kwargs):
        """
        Create a chown task.
        """
        super(ChownTask, self).__init__(*args, **kwargs)
        self.setMetadata('dispatch.split', True)
        self.setOption('user', '')
        self.setOption('group', '')

    def _perform(self):
        """
        Perform the task.
        """
        import grp
        import pwd

        alreadyDone = set()
        elements = self.elements()

        user = self.option('user')
        group = self.option('group')
        user = pwd.getpwnam(user).pw_uid
        group = grp.getgrnam(group).gr_gid

        for element in elements:
            filePath = element.var('filePath')

            if filePath in alreadyDone:
                continue
            else:
                alreadyDone.add(filePath)

            collectedFiles = self.__collectAllFiles(filePath)
            collectedFiles.sort(reverse=True)

            for collectedFile in collectedFiles:
                if os.path.islink(collectedFile):
                    continue

                os.chown(collectedFile, user, group)

        # default result based on the target filePath
        return super(ChownTask, self)._perform()

    @classmethod
    def __collectAllFiles(cls, path):
        """
        Return all files recursively from the given path.
        """
        result = [path]

        if os.path.isdir(path):
            for entry in os.listdir(path):
                fullPath = os.path.join(path, entry)
                if os.path.isdir(fullPath):
                    result += cls.__collectAllFiles(fullPath)
                else:
                    result.append(fullPath)
        return result


# registering task
Task.register(
    'chown',
    ChownTask
)
