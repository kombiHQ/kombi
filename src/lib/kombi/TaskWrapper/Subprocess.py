import os
import json
import platform
import tempfile
from ..EnvModifier import EnvModifier
from ..ProcessExecution import ProcessExecution
from .TaskWrapper import TaskWrapper, TaskWrapperError
from ..Task import Task
from ..Crawler import Crawler

class SubprocessFailedError(TaskWrapperError):
    """Subprocess failed Error."""

class Subprocess(TaskWrapper):
    """
    Abstract implementation designed to execute a task inside of a subprocess.
    """

    __serializedTaskEnv = "KOMBI_TASKWRAPPER_SUBPROCESS_FILE"

    def __init__(self, *args, **kwargs):
        """
        Create a task wrapper object.
        """
        super(Subprocess, self).__init__(*args, **kwargs)

        # options for tweaking the environment that is going to be used by
        # the process
        self.setOption('envPrepend', {})
        self.setOption('envAppend', {})
        self.setOption('envOverride', {})
        self.setOption('envUnset', [])

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
            kombi.TaskWrapper.Subprocess.runSerializedTask()
        """
        raise NotImplementedError

    def _commandPrefix(self):
        """
        For re-implementation: should return a string used as prefix for the command executed as subprocess.
        """
        # returning right away when no user is specified
        user = self.option('user')
        if user == '':
            return ''

        if platform.system() == "Windows":
            raise SubprocessFailedError(
                "Cannot change the user on current platform"
            )

        # otherwise in case the user starts with '$' means the value is driven by an environment variable.
        if user.startswith('$'):
            user = os.environ[user[1:]]

        # running as different user
        return 'su {} -c'.format(user)

    def _perform(self, task):
        """
        Implement the execution of the subprocess wrapper.
        """
        # execute process passing json
        serializedTaskFile = tempfile.NamedTemporaryFile(
            suffix='.json',
            mode='w',
            delete=False
        )
        serializedTaskFile.write(task.toJson())
        serializedTaskFile.close()

        # we need to make this temporary file R&W for anyone, since it may be manipulated by
        # a subprocess that uses a different user/permissions.
        os.chmod(serializedTaskFile.name, 0o777)

        # building full command executed as subprocess
        command = self._command()
        if self._commandPrefix():
            command = '{} "{}"'.format(
                self._commandPrefix(),
                command.replace('\\', '\\\\').replace('"', '\\"')
            )

        # adding the serializedTaskFile information
        envModifier = self.__envModifier()
        envModifier.setOverrideVar(
            self.__serializedTaskEnv,
            serializedTaskFile.name
        )

        processExecution = ProcessExecution(
            [
                command
            ],
            envModifier.generate(),
            shell=True
        )

        processExecution.execute()

        # checking if process has failed based on the return code
        if not processExecution.executionSuccess() and not self.option('ignoreExitCode'):
            raise SubprocessFailedError(
                'Error during the execution of the process, return code {}'.format(
                    processExecution.exitStatus()
                )
            )

        # the task passes the result by serializing it as json, we need to load the json file
        # and re-create the crawlers.
        result = []
        with open(serializedTaskFile.name) as jsonFile:
            for serializedJsonCrawler in json.load(jsonFile):
                result.append(
                    Crawler.createFromJson(serializedJsonCrawler)
                )

        # removing temporary file
        os.remove(serializedTaskFile.name)

        return result

    @staticmethod
    def runSerializedTask():
        """
        Run a serialized task defined in the environment during Subprocess._perform.
        """
        serializedTaskFilePath = os.environ[Subprocess.__serializedTaskEnv]
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
        with open(serializedTaskFilePath, 'w') as f:
            f.write(json.dumps(serializedCrawlers))

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
