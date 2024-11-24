from ..Task import Task

class ReduceOutputTask(Task):
    """
    Task used to modify the output by reducing the number of infoCrates.
    """

    def __init__(self, *args, **kwargs):
        """
        Create a modify infoCrates task object.
        """
        super(ReduceOutputTask, self).__init__(*args, **kwargs)

        self.setOption('total', 1)

    def _perform(self):
        """
        Perform the task.
        """
        return self.infoCrates()[:self.option('total')]


Task.register('reduceOutput', ReduceOutputTask)
