from ..Task import Task, TaskError

class ExternalTaskError(TaskError):
    """Base external task error."""

class ExternalTask(Task):
    """Base external task."""
