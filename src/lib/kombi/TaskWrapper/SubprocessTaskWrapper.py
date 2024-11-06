import os
import sys
import json
import inspect
import platform
import subprocess
import tempfile
import base64
import weakref
import signal
import atexit
from ..EnvModifier import EnvModifier
from .TaskWrapper import TaskWrapper, TaskWrapperError
from ..Task import Task
from ..Crawler import Crawler

class SubprocessTaskWrapperFailedError(TaskWrapperError):
    """Subprocess task wrapper failed Error."""

    __previousExceptionHook = None

    @classmethod
    def setupExceptionHook(cls):
        """
        Replace the current exception hook for the subprocess task wrapper exception hook.
        """
        # this method is only expected to be called once.
        assert cls.__previousExceptionHook is None

        cls.__previousExceptionHook = sys.excepthook
        sys.excepthook = cls.__exceptionHook

    @classmethod
    def __exceptionHook(cls, exctype, value, traceback):
        """
        Override for the error showed by the subprocess to print just one line error message.
        """
        if issubclass(exctype, cls):
            # The actual traceback/error raised by subprocess will be
            # already in the stdout/stderr stream
            sys.stdout.write("{}\n".format(value))
        else:
            cls.__previousExceptionHook(exctype, value, traceback)

class SubprocessTaskWrapper(TaskWrapper):
    """
    Abstract implementation designed to execute a task inside of a subprocess.
    """

    __serializedTaskEnv = "KOMBI_TASKWRAPPER_SUBPROCESS_FILE"
    __allSubprocessesWeakRef = []

    def __init__(self, *args, **kwargs):
        """
        Create a task wrapper object.
        """
        super(SubprocessTaskWrapper, self).__init__(*args, **kwargs)

        # options for tweaking the environment that is going to be used by
        # the process
        self.setOption('envPrepend', {})
        self.setOption('envAppend', {})
        self.setOption('envOverride', {})
        self.setOption(
            'envUnset', [
                # this variable may get defined automatically
                # when launching an application bundled with python
                # which can clash with other processes also bundled
                # with python. Therefore, letting those apps to
                # define it with the proper home information
                # as they get executed.
                'PYTHONHOME',
                'DISPLAY',
                'LD_LIBRARY_PATH'
            ]
        )
        self.setOption('timeout', 0)

        # tells the total number of instances that will be created to
        # execute the task as subprocesses. This effectively divides
        # the number of crawlers by the number of execution instances.
        # This is useful for tasks that don't use a lot of memory
        # /processing (Blocking I.O.). Therefore, they can be
        # executed in parallel, speeding up the entire execution.
        self.setOption('executionInstances', 1)

        # tells which user is going to run the process (leave empty to use
        # the current user)
        self.setOption('user', '')

        # this flag can be used to ignore the exit code of the process (
        # be careful with this flag)
        self.setOption('ignoreExitCode', False)

    def _command(self):
        """
        For re-implementation: should return a string which is executed as subprocess.

        The execution should trigger:
            kombi.TaskWrapper.SubprocessTaskWrapper.runSerializedTask()
        """
        raise NotImplementedError

    def _perform(self, task):
        """
        Implement the execution of the subprocess wrapper.
        """
        processes = {}
        executionInstances = self.option('executionInstances')
        clonedTask = task.clone()
        originalCrawlers = task.crawlers()

        totalCrawlersPerPerform = int(round(len(originalCrawlers) / float(executionInstances)))
        for i in range(executionInstances):
            currentIndex = i * totalCrawlersPerPerform
            nextIndex = currentIndex + totalCrawlersPerPerform if i < executionInstances - 1 else None
            taskCrawlers = originalCrawlers[currentIndex:nextIndex]

            if not taskCrawlers:
                continue

            # cleaning all crawlers in the task
            # we are going to add them back in groups
            clonedTask.clear()

            # adding crawlers back to the cloned task
            for taskCrawler in taskCrawlers:
                clonedTask.add(taskCrawler, task.target(taskCrawler))

            # execute process passing json
            serializedTaskFile = tempfile.NamedTemporaryFile(
                prefix="serializedTask_",
                suffix='.json',
                mode='w',
                delete=False
            )
            taskJsonData = clonedTask.toJson()
            serializedTaskFile.write(taskJsonData)
            serializedTaskFile.close()

            # we need to make this temporary file R&W for anyone, since it may be manipulated by
            # a subprocess that might use a different user/permissions.
            os.chmod(serializedTaskFile.name, 0o777)

            # adding the serializedTaskFile information
            envModifier = self.__envModifier()
            envModifier.setOverrideVar(
                self.__serializedTaskEnv,
                serializedTaskFile.name
            )

            # building full command executed as subprocess
            command = self._command()
            env = envModifier.generate()

            # printing command in the stdout (for logging purposes)
            sys.stdout.write("{}\n".format(command))

            # when command needs to be used under a different user
            if self.option('user'):
                assert platform.system() == "Linux", "Platform not supported!"

                runCommand = os.path.join(
                    os.path.dirname(
                        os.path.realpath(__file__)
                    ),
                    'auxiliary',
                    'runCommand.py'
                )

                command = 'su -l {} -s /bin/bash -c "python {} \'{}\'"'.format(
                    self.option('user'),
                    runCommand,
                    base64.b64encode(
                        json.dumps(
                            {
                                'command': command,
                                'env': env
                            }
                        ).encode('utf-8')
                    ).decode('ascii')
                )

            # creating subprocess
            process = subprocess.Popen(
                command,
                stderr=subprocess.STDOUT,
                env=env,
                shell=True,
                preexec_fn=os.setsid
            )

            # in case the python process is terminated we want to keep
            # track of all sub processes so they can be
            # terminated as well
            self.__allSubprocessesWeakRef.append(weakref.ref(process))

            processes[process] = serializedTaskFile.name

        result = []
        for process, serializedTaskFileName in processes.items():
            # timeout execution
            waitArgs = {}
            useTimeOut = self.option('timeout') or None
            if 'timeout' in inspect.getfullargspec(process.wait).args:
                waitArgs['timeout'] = useTimeOut
            elif useTimeOut is not None:
                sys.stderr.write('Timeout is not supported in the execution of the subprocess for current python version, skipping it!\n')

            # waiting for execution
            process.wait(**waitArgs)

            # checking if process has failed based on the return code
            if process.returncode and not self.option('ignoreExitCode'):

                # now raising the exception
                raise SubprocessTaskWrapperFailedError(
                    'Error during the execution of the process, return code {}'.format(
                        process.returncode
                    )
                )

            # the task passes the result by serializing it as json, we need to load the json file
            # and re-create the crawlers.
            with open(serializedTaskFileName) as jsonFile:
                taskResultDataJson = jsonFile.read()

                # making sure the result has been created.
                if taskResultDataJson == taskJsonData:
                    raise SubprocessTaskWrapperFailedError(
                        'Failed to retrieve task result from subprocess!'
                    )

                for serializedJsonCrawler in json.loads(taskResultDataJson):
                    result.append(
                        Crawler.createFromJson(serializedJsonCrawler)
                    )

            # removing temporary file
            os.remove(serializedTaskFileName)

        return result

    @staticmethod
    def runSerializedTask():
        """
        Run a serialized task defined in the environment during SubprocessTaskWrapper._perform.
        """
        serializedTaskFilePath = os.environ[SubprocessTaskWrapper.__serializedTaskEnv]
        serializedJsonTaskContent = None
        with open(serializedTaskFilePath) as jsonFile:
            serializedJsonTaskContent = jsonFile.read()

        # re-creating the task from the json contents
        task = Task.createFromJson(serializedJsonTaskContent)

        # running task and serializing the output as json.
        serializedCrawlers = []
        for crawler in task.output():
            serializedCrawlers.append(crawler.toJson())

        # we use the environment to tell where the result has been serialized
        # so it can be resulted back by the parent process.
        with open(serializedTaskFilePath, 'r+') as f:
            # erasing the contents of the file. This is necessary since the
            # file may be owned by a different user (happens when
            # running a task wrapper with the option 'user' defined)
            f.truncate(0)
            # writing the output
            f.write(json.dumps(serializedCrawlers))

    @classmethod
    def killAllSubProcesses(cls):
        """
        Ensure all sub processes are terminated when python is terminated.
        """
        for processStillRunning in filter(lambda x: x() is not None and x().poll() is None, cls.__allSubprocessesWeakRef):
            sys.stderr.write(
                "Terminating sub-process, pid: {}\n".format(
                    processStillRunning().pid
                )
            )

            # trying to kill the subprocess
            try:
                os.kill(processStillRunning().pid, signal.SIGKILL)
            except Exception:
                sys.stderr.write(
                    "Error on terminating sub-process, pid: {}\n".format(
                        processStillRunning().pid
                    )
                )
            sys.stderr.flush()

    def __envModifier(self):
        """
        Return an Env Modifier instance.

        This instance is based on the current environment and
        populated with the options related with the environment tweaks.
        """
        # creating an env modifier object
        envModifier = EnvModifier(os.environ)

        # prepend
        for varName, varValue in self.option('envPrepend').items():
            envModifier.addPrependVar(
                varName,
                varValue
            )

        # append
        for varName, varValue in self.option('envAppend').items():
            envModifier.addAppendVar(
                varName,
                varValue
            )

        # override
        for varName, varValue in self.option('envOverride').items():
            envModifier.setOverrideVar(
                varName,
                varValue
            )

        # unset
        for varName in self.option('envUnset'):
            envModifier.addUnsetVar(varName)

        return envModifier


# adding a hook to terminate all subprocess is running when the
# current python process is terminated
atexit.register(SubprocessTaskWrapper.killAllSubProcesses)

try:
    signal.signal(signal.SIGTERM, SubprocessTaskWrapper.killAllSubProcesses)
    signal.signal(signal.SIGINT, SubprocessTaskWrapper.killAllSubProcesses)
except Exception:
    pass

# replacing the current exception hook
SubprocessTaskWrapperFailedError.setupExceptionHook()
