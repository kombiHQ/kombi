from kombi.Task import Task

class EchoTask(Task):
    """
    Dummy task used to check the output.
    """


Task.register(
    'echoTask',
    EchoTask
)
