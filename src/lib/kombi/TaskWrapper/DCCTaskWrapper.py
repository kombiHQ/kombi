from .SubprocessTaskWrapper import SubprocessTaskWrapper

class DCCTaskWrapper(SubprocessTaskWrapper):
    """
    ABC to perform a task inside of a dcc (like maya, nuke...).
    """

    def _perform(self, task):
        """
        Implement the execution of the subprocess wrapper.
        """
        # execute the task right away
        return task.output()

    def _command(self):
        """
        For re-implementation: should return a string which is executed as subprocess.
        """
        raise NotImplementedError

    @classmethod
    def _hookName(cls):
        """
        For re-implementation: should return a string containing the name used for the hook registered in basetools.
        """
        raise NotImplementedError
