import os
import re
import sys
import subprocess
from threading import Thread

try:
    from queue import Queue, Empty  # python 3
except ImportError:
    from Queue import Queue, Empty  # python 2

class ProcessExecution(object):
    """
    Executes a process.
    """

    # regex: any alpha numeric, underscore and dash characters are allowed.
    __validateShellArgRegex = re.compile(r"^[\w_-]*$")

    def __init__(self, args, env=None, shell=True, cwd=None, redirectStderrToStdout=False):
        """
        Create a ProcessExecution object.

        The constructor signature tries mimic the features available by subprocess.Popen.
        """
        if env is None:
            env = dict(os.environ)

        self.__stdout = []
        self.__stderr = []
        self.__shell = shell
        self.__cwd = cwd
        self.__redirectStderrToStdout = redirectStderrToStdout

        self.__setArgs(args)
        self.__setEnv(env)
        self.__createProcess()

    def isShell(self):
        """
        Return the process should run through a shell session.
        """
        return self.__shell

    def env(self):
        """
        Return the environment for the process.
        """
        return self.__env

    def cwd(self):
        """
        Return the current working directory used to launch the process.
        """
        return self.__cwd

    def args(self):
        """
        Return a list of arguments used by the process.
        """
        return self.__args

    def stdout(self):
        """
        Return a list of stdout messages.
        """
        return self.__stdout

    def redirectStderrToStdout(self):
        """
        Return a boolean telling if the stderr stream should be redirected to stdout.
        """
        return self.__redirectStderrToStdout

    def executionSuccess(self):
        """
        Return a boolean if the execution has been successfully.
        """
        return self.exitStatus() == 0

    def exitStatus(self):
        """
        Return the exist status about the process.
        """
        return self.__process.returncode

    def pid(self):
        """
        Return the process id.
        """
        return self.__process.pid

    def execute(self):
        """
        Execute the process.
        """
        # stdout queue
        stdoutQueue = Queue()
        stdoutThread = Thread(
            target=self.__readStreamToQueue,
            args=(self.__process.stdout, stdoutQueue)
        )
        stdoutThread.daemon = True  # thread dies with the program
        stdoutThread.start()

        # stderr queue
        stderrQueue = None
        stderrThread = None
        if not self.redirectStderrToStdout():
            stderrQueue = Queue()
            stderrThread = Thread(
                target=self.__readStreamToQueue,
                args=(self.__process.stderr, stderrQueue)
            )
            stderrThread.daemon = True  # thread dies with the program
            stderrThread.start()

        # retrieving value from queue
        while stdoutThread.is_alive() or (stderrThread is not None and stderrThread.is_alive()):

            # stdout
            stdoutValue = self.__queryStreamValueFromQueue(stdoutQueue)
            if stdoutValue is not None:
                sys.stdout.write(stdoutValue)
                sys.stdout.flush()
                self.__stdout.append(stdoutValue)

            # stderr
            if stderrQueue is None:
                continue

            stderrValue = self.__queryStreamValueFromQueue(stderrQueue)
            if stderrValue is not None:
                sys.stderr.write(stderrValue)
                sys.stderr.flush()
                self.__stderr.append(stderrValue)

        self.__process.wait()

    def __setArgs(self, args):
        """
        Set a list of arguments that should be used by the process.
        """
        assert isinstance(args, (list, tuple)), "Invalid args list!"

        self.__args = list(args)

    def __setEnv(self, env):
        """
        Set the environment for the process.
        """
        self.__env = dict(env)

    def __createProcess(self):
        """
        Create a process that later should be executed through {@link run}.
        """
        stderrStream = subprocess.STDOUT if self.redirectStderrToStdout() else subprocess.PIPE

        executableArgs = ' '.join(self.__sanitizeShellArgs(self.args())) if self.isShell() else self.args()
        self.__process = subprocess.Popen(
            executableArgs,
            bufsize=1,
            close_fds='posix' in sys.builtin_module_names,
            stdout=subprocess.PIPE,
            stderr=stderrStream,
            shell=self.isShell(),
            env=self.env(),
            cwd=self.cwd()
        )

    @classmethod
    def __readStreamToQueue(cls, outStream, queue):
        """
        Read the stream and add its contents to a queue.
        """
        for line in iter(outStream.readline, b''):
            queue.put(line)
        outStream.close()

    @classmethod
    def __queryStreamValueFromQueue(cls, queue):
        """
        Return the stream value from the queue or None in case the queue is empty.
        """
        result = None
        try:
            line = queue.get_nowait()
        except Empty:
            pass
        else:
            if not isinstance(line, str):
                line = line.decode("utf_8")
            result = line

        return result

    @staticmethod
    def __sanitizeShellArgs(args):
        """
        Sanitize shell args by escaping shell special characters.
        """
        result = []

        for index, arg in enumerate(args):
            arg = str(arg)

            # we need to avoid to escape the first argument otherwise, it will be
            # interpreted as string rather than a command.
            if index == 0 or ProcessExecution.__validateShellArgRegex.match(arg):
                result.append(arg)
            else:
                result.append('"{}"'.format(arg.replace('"', '\\"')))

        return result