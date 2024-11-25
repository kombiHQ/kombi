import os
import subprocess
import getpass
import tempfile
from ..Dispatcher import DispatcherError
from .RenderfarmDispatcher import RenderfarmDispatcher
from .Job import Job, CollapsedJob, ExpandedJob

class DeadlineDispatcherCommandError(DispatcherError):
    """Deadline command error."""

class DeadlineDispatcher(RenderfarmDispatcher):
    """
    Deadline dispatcher implementation.

    Note for potential issues in deadline:
        - Make sure the "CommandLine" plugin is enabled in deadline.
        - The python executable called through command-line can be defined through the
        environment variable: KOMBI_PYTHON_EXECUTABLE (when not defined it defaults
        to python), you may need to provide the full qualified location for the python executable
        on windows (for instance: KOMBI_PYTHON_EXECUTABLE=X:/apps/python37/python.exe).

    Optional options: pool, secondaryPool, group and jobFailRetryAttempts
    """

    __deadlineCommandExecutable = os.environ.get('KOMBI_DEADLINECOMMAND_EXECUTABLE', 'deadlinecommand')
    __defaultGroup = os.environ.get('KOMBI_DISPATCHER_RENDERFARM_GROUP', '')
    __defaultPool = os.environ.get('KOMBI_DISPATCHER_RENDERFARM_POOL', '')
    __defaultSecondaryPool = os.environ.get('KOMBI_DISPATCHER_RENDERFARM_SECONDARYPOOL', '')
    __defaultJobFailRetryAttempts = 10

    def __init__(self, *args, **kwargs):
        """
        Create a RenderfarmDispatcher dispatcher object.
        """
        super(DeadlineDispatcher, self).__init__(*args, **kwargs)

        # setting default options
        self.setOption('group', self.__defaultGroup)
        self.setOption('pool', self.__defaultPool)
        self.setOption('secondaryPool', self.__defaultSecondaryPool)
        self.setOption('jobFailRetryAttempts', self.__defaultJobFailRetryAttempts)

        # additional props that can be passed to deadline
        self.setOption('additionalProps', {})

        # deadline is extremely slow to submit jobs to the farm. Therefore,
        # we need to expand them inside of the farm rather than awaiting
        # locally for the submission of all the jobs.
        self.setOption('expandOnTheFarm', True)

        # for the same performance reason above we want to let deadline to chunkify
        # the job on the farm by default
        self.setOption('chunkifyOnTheFarm', True)

        # tells if the dispatcher should inheritance the priority based on the parent
        # job (default). Disable this option when you want to ignore any current
        # priority that has been set/overridden in the parent jobs
        self.setOption('priorityInherintance', True)

    def option(self, name, *args, **kwargs):
        """
        Return a value from an option.

        Due several performance penalty caused by querying deadline command
        we need to compute 'groupNames' and 'poolNames' only when they are queried.
        """
        # computing dynamic option
        if name not in self.optionNames() and name in ['groupNames', 'poolNames']:
            if name == 'groupNames':
                command = '{} GetGroupNames'.format(self.__deadlineCommandExecutable)
            else:
                command = '{} GetPoolNames'.format(self.__deadlineCommandExecutable)

            self.setOption(
                name,
                self.__executeDeadlineCommand(
                    command
                ).split('\n')
            )

        # returning the value for an option
        return super(DeadlineDispatcher, self).option(name, *args, **kwargs)

    def _addDependencyIds(self, jobId, dependencyIds, task=None):
        """
        For re-implementation: Should add the dependency ids to the input job id.

        This feature is used when a collapsed job is expanded on the farm. Therefore,
        all the jobs created by the collapsed job should be added back
        as dependency of the collapsed job itself. Also, you may need to mark
        the collapsed job as pending status again.
        """
        # getting the current job ids
        currentJobIds = self.__executeDeadlineCommand(
            "{} GetJobSetting {} JobDependencies".format(self.__deadlineCommandExecutable, jobId)
        )

        currentJobIds = currentJobIds.split(",") if len(currentJobIds) else []

        # appending with the new dependency ids
        currentJobIds += dependencyIds

        # updating the job dependency ids
        currentJobIds = self.__executeDeadlineCommand(
            "{} SetJobSetting {} JobDependencies {}".format(
                self.__deadlineCommandExecutable,
                jobId,
                ','.join(dependencyIds)
            )
        )

        # marking job as pending again
        self.__executeDeadlineCommand(
            "{} PendJob {}".format(
                self.__deadlineCommandExecutable,
                jobId
            )
        )

        # updating original priority (since it may have been changed
        # on the farm)
        if self.option('priorityInherintance', task):
            currentPriority = self.__executeDeadlineCommand(
                "{} GetJobSetting {} Priority".format(
                    self.__deadlineCommandExecutable,
                    jobId
                )
            )

            for dependencyId in dependencyIds:
                self.__executeDeadlineCommand(
                    "{} SetJobSetting {} Priority {}".format(
                        self.__deadlineCommandExecutable,
                        dependencyId,
                        currentPriority
                    )
                )

    def _executeOnTheFarm(self, renderfarmJob, jobDataFilePath):
        """
        For re-implementation: Should call the subprocess that dispatches the job to the farm.

        Should return the job id created during the dispatching.
        """
        assert isinstance(renderfarmJob, Job), \
            "Invalid RenderFarmJob type!"

        task = renderfarmJob.taskHolder().task()
        dependencyIds = renderfarmJob.dependencyIds()
        outputDirectories = []

        # computing the command that deadline is going to trigger on the farm
        command = '{0} {1}'.format(
            os.path.join(os.path.dirname(os.path.realpath(__file__)), "auxiliary", "execute-renderfarm.py"),
            jobDataFilePath
        )

        # in case "chunkifyOnTheFarm" is enabled we need to add the parameters about
        # the start frame and end frame. Deadline is going to provide the value
        # for them when computing the chunks on the farm
        if self.option('chunkifyOnTheFarm') and isinstance(renderfarmJob, ExpandedJob) and renderfarmJob.chunkSize():
            command += " --range-start <STARTFRAME> --range-end <ENDFRAME>"

        args = self.__defaultJobArgs(
            task,
            command,
            jobDataFilePath
        )

        # collapsed job
        if isinstance(renderfarmJob, CollapsedJob):
            # adding the job name
            args += [
                "-name",
                "Pending {}".format(task.type())
            ]

            # since pending jobs are intermediated jobs, we mark them to be deleted asap
            # they are completed
            args += [
                "-prop",
                "OnJobComplete=Delete"
            ]

        # expanded job type
        else:
            totalChunks = renderfarmJob.chunkTotal()
            currentChunk = renderfarmJob.currentChunk()

            # label displayed in deadline
            taskLabel = task.type()

            if self.option('chunkifyOnTheFarm') and renderfarmJob.chunkSize():
                args += [
                    "-prop",
                    "Frames=0-{}".format(renderfarmJob.totalInChunk() - 1),
                    "-prop",
                    "ChunkSize={}".format(renderfarmJob.chunkSize())
                ]
            else:
                taskLabel += ' ({}/{}): '.format(
                    str(currentChunk + 1).zfill(3),
                    str(totalChunks).zfill(3)
                )

            taskLabel = "{} {}".format(
                taskLabel,
                task.elements()[0].var('name')
            )

            args += [
                "-name",
                task.metadata('label') if task.hasMetadata('label') else taskLabel
            ]

            # adding additional props
            hasOutputDirectory = False
            for keyProp, valueProp in self.option('additionalProps').items():
                if keyProp.startswith('OutputDirectory'):
                    hasOutputDirectory = True

                args += [
                    "-prop",
                    "{}={}".format(keyProp, valueProp)
                ]

            # output directories
            if not hasOutputDirectory:
                outputDirectories = list(filter(lambda x: bool(x), set(map(lambda x: os.path.dirname(task.target(x)), task.elements()))))
                for index, outputDirectory in enumerate(outputDirectories):
                    args += [
                        "-prop",
                        "OutputDirectory{}={}".format(index, outputDirectory)
                    ]

        if dependencyIds:
            args += [
                "-prop",
                "JobDependencies=" + ",".join(dependencyIds)
            ]

        output = self.__executeDeadlineCommand(
            ' '.join([
                self.__deadlineCommandExecutable,
                self.__serializeDeadlineArgs(args, renderfarmJob.jobDirectory())
            ]),
        )

        jobIdPrefix = "JobID="
        jobId = list(filter(lambda x: x.startswith(jobIdPrefix), output.split("\n")))

        if jobId:
            # it should contain just a single job id
            return jobId[0][len(jobIdPrefix):]
        else:
            raise DeadlineDispatcherCommandError(output)

    def __defaultJobArgs(self, task, command, jobDataFilePath):
        """
        Return a list containing the default job args that later are passed to deadlinecommand.
        """
        pythonExec = self.option('env').get(
            'KOMBI_PYTHON_EXECUTABLE',
            'python'
        )
        kombiUser = self.option('env').get('KOMBI_USER', getpass.getuser())

        args = [
            "-SubmitCommandLineJob",
            "-executable",
            pythonExec,
            "-arguments",
            command,
            "-priority",
            '{}'.format(
                self.option(
                    'priority',
                    task
                )
            ),
            "-prop",
            "OverrideJobFailureDetection=true",
            "-prop",
            "FailureDetectionJobErrors={}".format(self.option('jobFailRetryAttempts', task) + 1),
            "-prop",
            "IncludeEnvironment=true",
            "-prop",
            "BatchName={}".format(self.option('label')),
            "-prop",
            "UserName={}".format(kombiUser)
        ]

        # adding optional props
        for optionName in ('group', 'pool', 'secondaryPool'):
            if self.option(optionName, task):
                args += [
                    "-prop",
                    "{}={}".format(
                        optionName.capitalize(),
                        self.option(
                            optionName,
                            task
                        )
                    )
                ]

        return args

    def __serializeDeadlineArgs(self, args, directory):
        """
        Return a file path about the serialized args.
        """
        temporaryFile = tempfile.NamedTemporaryFile(
            mode='w',
            prefix=os.path.join(directory, "deadline_"),
            suffix='.txt',
            delete=False
        )
        temporaryFile.write('\n'.join(map(str, args)))
        temporaryFile.close()

        return temporaryFile.name

    def __executeDeadlineCommand(self, command):
        """
        Auxiliary method used to execute a deadline command.
        """
        process = subprocess.Popen(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=self.option('env')
        )

        # capturing the output
        output, error = process.communicate()

        if error:
            raise DeadlineDispatcherCommandError(error.decode("utf-8"))

        return output.decode("utf-8")


# registering dispatcher
DeadlineDispatcher.register(
    'renderFarm',
    DeadlineDispatcher
)
