from ..Task import Task

class ReduceOutputTask(Task):
    """
    Task used to modify the output by reducing the number of elements.
    """

    def __init__(self, *args, **kwargs):
        """
        Create a modify elements task object.
        """
        super(ReduceOutputTask, self).__init__(*args, **kwargs)

        self.setOption('total', 1)

    def _perform(self):
        """
        Perform the task.
        """
        return self.elements()[:self.option('total')]


Task.register('reduceOutput', ReduceOutputTask)
