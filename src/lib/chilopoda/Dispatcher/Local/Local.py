import os
import sys
import subprocess
import tempfile
import threading
from ..Dispatcher import Dispatcher, DispatcherError
from ...ProcessExecution import ProcessExecution

class LocalExecutionError(DispatcherError):
    """Local Execution Error."""

class _ProcessExecutionThread(threading.Thread):
    """
    Thread used to execute the sub-process.
    """

    def __init__(self, processExecution):
        """
        Create a process execution thread.
        """
        assert isinstance(processExecution, ProcessExecution), \
            "Invalid processExecution type!"

        super(_ProcessExecutionThread, self).__init__()
        self.__processExecution = processExecution

    def run(self):
        """
        Run the thread.
        """
        self.__processExecution.execute()

        if self.__processExecution.exitStatus():
            raise LocalExecutionError('\n'.join(self.__processExecution.stdoutContent()))

class Local(Dispatcher):
    """
    Local dispatcher implementation.

    Dispatches the task holder as sub-process and returns
    the process id. The sub-process is executed in a separated
    thread by default.
    """

    __runningThreads = []
    __defaultAwaitExecution = False

    def __init__(self, *args, **kwargs):
        """
        Create a local dispatch instance.
        """
        super(Local, self).__init__(*args, **kwargs)

        self.setStdout(sys.stdout)
        self.setStderr(subprocess.STDOUT)

        self.setOption(
            "awaitExecution",
            self.__defaultAwaitExecution
        )

    def setStdout(self, stream):
        """
        Set the stdout stream used for the process execution.
        """
        self.__stdout = stream

    def stdout(self):
        """
        Return the stdout stream.
        """
        return self.__stdout

    def setStderr(self, stream):
        """
        Set the stderr stream used for the process execution.
        """
        self.__stderr = stream

    def stderr(self):
        """
        Return the stderr stream.
        """
        return self.__stderr

    def _perform(self, taskHolder):
        """
        Execute the dispatcher.
        """
        self.cleanup()

        pythonExec = os.environ.get(
            'CHILOPODA_PYTHON_EXECUTABLE',
            'python'
        )

        processExecution = ProcessExecution(
            [
                pythonExec,
                os.path.join(
                    os.path.dirname(
                        os.path.realpath(__file__)
                    ),
                    "auxiliary",
                    "execute-local.py"
                ),
                self.__bakeTaskHolderToJson(taskHolder)
            ],
            self.option('env'),
            shell=True,
            stdout=self.stdout(),
            stderr=self.stderr()
        )

        # executing process
        if self.option('awaitExecution'):
            processExecution.execute()
            if processExecution.exitStatus():
                raise LocalExecutionError('\n'.join(processExecution.stdoutContent()))

        # otherwise delegating the execution to a thread
        else:
            # creating a new thread that is going to deal
            # the process execution
            processThread = _ProcessExecutionThread(processExecution)

            self.__runningThreads.append(processThread)

            # start the thread that is going to execute the process.
            processThread.start()

        return [
            processExecution
        ]

    @classmethod
    def cleanup(cls):
        """
        Clean up all the finished threads dispatched previously.
        """
        # cleaning up previous threads that have been finished
        removedIndex = 0
        for index, runningThread in enumerate(list(cls.__runningThreads)):
            if not runningThread.is_alive():
                del cls.__runningThreads[index - removedIndex]
                removedIndex += 1

    @classmethod
    def __bakeTaskHolderToJson(cls, taskHolder):
        """
        Return the file path for the input serialized taskHolder.
        """
        temporaryFile = tempfile.NamedTemporaryFile(
            mode='w',
            prefix="local_",
            suffix='.json',
            delete=False
        )
        temporaryFile.write(taskHolder.toJson())
        temporaryFile.close()

        return temporaryFile.name


# registering dispatcher
Local.register(
    'local',
    Local
)
