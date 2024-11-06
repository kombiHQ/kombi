import os
import getpass
import json
import uuid
from datetime import datetime
from collections import OrderedDict
from ..Dispatcher import Dispatcher
from .Job import Job, ExpandedJob, CollapsedJob

class RenderfarmDispatcher(Dispatcher):
    """
    Abstracted implementation for a renderfarm dispatcher.

    Optional options: label, jobTempDir, splitSize, priority, chunkifyOnTheFarm and expandOnTheFarm
    """

    __defaultJobTempDir = os.environ.get('KOMBI_TEMP_REMOTE_DIR', '')
    __defaultLabel = "kombi"
    __defaultExpandOnTheFarm = False
    __defaultChunkifyOnTheFarm = False
    __defaultPriority = int(os.environ.get('KOMBI_DISPATCHER_RENDERFARM_PRIORITY', 50))
    __defaultSplitSize = int(os.environ.get('KOMBI_DISPATCHER_RENDERFARM_SPLITSIZE', 10))

    def __init__(self, *args, **kwargs):
        """
        Create a Renderfarm dispatcher object.
        """
        super(RenderfarmDispatcher, self).__init__(*args, **kwargs)

        assert len(self.__defaultJobTempDir), "KOMBI_TEMP_REMOTE_DIR env is not defined!"

        # setting default options
        self.setOption('label', self.__defaultLabel)
        self.setOption('jobTempDir', self.__defaultJobTempDir)
        self.setOption('splitSize', self.__defaultSplitSize)
        self.setOption('priority', self.__defaultPriority)
        self.setOption('expandOnTheFarm', self.__defaultExpandOnTheFarm)
        self.setOption('chunkifyOnTheFarm', self.__defaultChunkifyOnTheFarm)

    def extendDependencyIds(self, jobId, dependencyIds, task=None):
        """
        Extend the dependencies in the input job id.
        """
        assert isinstance(dependencyIds, list), "dependencyIds should be a list!"

        self._addDependencyIds(
            jobId,
            dependencyIds,
            task
        )

    def _addDependencyIds(self, jobId, dependencyIds, task=None):
        """
        For re-implementation: Should add the dependency ids to the input job id.

        This is feature used when a collapsed job is expanded on the farm. Therefore,
        all the jobs created by the collapsed job should be added back
        as dependency of the collapsed job itself. Also, you may need to mark
        the collapsed job as pending status again.
        """
        raise NotImplementedError

    def _perform(self, taskHolder):
        """
        Execute the dispatcher.

        Return a list of job ids.
        """
        clonedTaskHolder = taskHolder.clone()
        jobDirectory = self.__createJobDirectory()
        renderfarmJobs = []

        if self.option('expandOnTheFarm'):
            collapsedJob = CollapsedJob(
                taskHolder,
                jobDirectory
            )

            jobDataFilePath = self.__generateJobData(
                collapsedJob
            )

            # sending to the farm
            return [
                self._executeOnTheFarm(
                    collapsedJob,
                    jobDataFilePath
                )
            ]

        else:
            renderfarmJobs += self.__dispatchMainTaskHolder(
                clonedTaskHolder,
                jobDirectory
            )

        renderfarmJobs += self.__dispatchSubTaskHolders(
            clonedTaskHolder.subTaskHolders(),
            jobDirectory,
            renderfarmJobs
        )

        return list(map(lambda x: x.jobId(), renderfarmJobs))

    def _executeOnTheFarm(self, renderfarmJob, jobDataFilePath):
        """
        For re-implementation: Should dispatch the job to the farm.

        Make sure the implementation returns the job id created during the dispatch. Also,
        in case you want the renderfarm manager itself to deal with the chunkfication
        of the task (available through "chunkifyOnTheFarm" option) you can query the
        information about the chunk through ExpandedJob object which is passed
        via renderfarmjob argument.
        """
        raise NotImplementedError

    def __generateJobData(self, renderfarmJob):
        """
        Generate a file used to execute the task holder on the farm.
        """
        assert isinstance(renderfarmJob, Job), \
            "Invalid Job type!"

        # in case the option "expandOnTheFarm" is enabled we need to disable that
        # otherwise, the job is going to keep re-spawning on the farm indefinitely.
        renderFarmDispatcher = self
        if renderFarmDispatcher.option('expandOnTheFarm'):
            renderFarmDispatcher = renderFarmDispatcher.createFromJson(
                renderFarmDispatcher.toJson()
            )

            renderFarmDispatcher.setOption(
                'expandOnTheFarm',
                False
            )

        data = {
            'dispatcher': renderFarmDispatcher.toJson(),
            'taskHolder': renderfarmJob.taskHolder().toJson()
        }

        # collapsed job
        if isinstance(renderfarmJob, CollapsedJob):
            data['jobType'] = 'collapsed'
            data['taskInputFilePaths'] = []

            # adding the result of expanded jobs. This information is going
            # to be used as input when the job gets expanded
            for expandedJob in renderfarmJob.expandedJobs():
                data['taskInputFilePaths'].append(
                    expandedJob.taskResultFilePath()
                )

        # expanded job
        else:
            data['jobType'] = 'expanded'
            data['taskResultFilePath'] = renderfarmJob.taskResultFilePath()

        jobDataFilePath = os.path.join(
            renderfarmJob.jobDirectory(),
            "jobData_{}.json".format(
                str(uuid.uuid4())
            )
        )

        # writing out the job data
        with open(jobDataFilePath, 'w') as outputFile:
            json.dump(
                data,
                outputFile,
                indent=4
            )

        # we might need to open this file with a different
        # user to append the output
        # (in case the task runs a different user)
        os.chmod(jobDataFilePath, 0o777)

        return jobDataFilePath

    def __dispatchMainTaskHolder(self, taskHolder, jobDirectory):
        """
        Dispatch the main task holder as expanded jobs on the farm.

        The result is a list of expanded job instances.
        """
        clonedTaskHolder = taskHolder.clone(includeSubTaskHolders=False)
        task = clonedTaskHolder.task()
        result = []

        # figuring out how the task is going to split the crawlers in multiple
        # tasks. In case the split size is assigned to 0 means the task is not
        # going to be divided
        splitSize = 0
        if task.hasMetadata('dispatch.split') and task.metadata('dispatch.split'):
            if task.hasMetadata('dispatch.splitSize'):
                splitSize = task.metadata('dispatch.splitSize')
            else:
                splitSize = self.option('splitSize')

        # querying all crawlers from the current task so we can re-assign them
        # back to the task in chunks (when split size is greater than 0)
        taskCrawlers = OrderedDict()
        for index, crawler in enumerate(task.crawlers()):
            # we are adding the tag 'originalIndex' to the crawlers, so even if they get
            # executed in chunks we can get to know their original index. Useful,
            # when you want to executed a single operation among all chunks:
            # if originalIndex == 0 do something...
            crawler.setTag('originalIndex', index)
            taskCrawlers[crawler] = task.target(crawler)

        # we can delegate the chunkfication to the render farm dispatcher
        # when chunkifyOnTheFarm is enabled. Otherwise, we chunkify
        # by splitting in sub jobs
        crawlers = list(taskCrawlers.keys())
        if self.option('chunkifyOnTheFarm') or splitSize == 0:
            chunkfiedCrawlers = [crawlers]
        else:
            chunkfiedCrawlers = self.__chunkify(crawlers, splitSize)

        # splitting in multiple tasks
        for index, chunkedCrawlers in enumerate(chunkfiedCrawlers):

            # creating a renderfarm job
            expandedJob = ExpandedJob(clonedTaskHolder, jobDirectory)

            # adding information about the chunks
            expandedJob.setChunkTotal(len(chunkfiedCrawlers))
            expandedJob.setCurrentChunk(index)
            expandedJob.setTotalInChunk(len(chunkedCrawlers))
            expandedJob.setChunkSize(splitSize)

            task = clonedTaskHolder.task()

            # adding crawlers to the task (since the task holder has been cloned
            # previously it's safe for us to change it)
            task.clear()
            for chunkedCrawler in chunkedCrawlers:
                targetFilePath = taskCrawlers[chunkedCrawler]
                task.add(chunkedCrawler, targetFilePath)

            jobDataFilePath = self.__generateJobData(
                expandedJob
            )

            # sending to the farm
            jobId = self._executeOnTheFarm(
                expandedJob,
                jobDataFilePath
            )

            # setting the job id to the expanded job. This information may
            # be used by sub tasks holders.
            expandedJob.setJobId(jobId)

            result.append(
                expandedJob
            )

        return result

    def __dispatchSubTaskHolders(self, subTaskHolders, jobDirectory, renderfarmJobs):
        """
        Dispatch the sub task holders as collapsed jobs on the farm.

        The result is a list of collapsed job instances.
        """
        result = []
        awaitSubtaskHolders = []

        # processing first all sub task holders that can be executed in parallel
        for subTaskHolder in subTaskHolders:
            if subTaskHolder.task().hasMetadata('dispatch.await') and subTaskHolder.task().metadata('dispatch.await'):
                awaitSubtaskHolders.append(subTaskHolder)
                continue

            collapsedJob = CollapsedJob(
                subTaskHolder,
                jobDirectory
            )

            # adding the input renderfarm jobs as dependency
            for renderfarmJob in renderfarmJobs:
                collapsedJob.addExpandedJob(renderfarmJob)
                collapsedJob.addDependencyId(renderfarmJob.jobId())

            jobDataFilePath = self.__generateJobData(
                collapsedJob
            )

            # sending to the farm
            jobId = self._executeOnTheFarm(
                collapsedJob,
                jobDataFilePath
            )

            # setting the job id to the collapsed job
            collapsedJob.setJobId(jobId)

            self.__createJobIdFile(
                jobDataFilePath,
                jobId
            )

            result.append(collapsedJob)

        # processing the awaiting sub-tasks holders. When a sub task holder is marked with
        # "await" means it is only going to be started after all the sub task holders are done,
        # making the sub task holder to be executed in a stack model rather than
        # in a parallel model.
        parentRenderfarmJobs = result
        for awaitSubtaskHolder in awaitSubtaskHolders:

            collapsedJob = CollapsedJob(
                awaitSubtaskHolder,
                jobDirectory
            )

            # adding all the expanded jobs passed as argument to this
            # method to the collapsed jobs
            for renderfarmJob in renderfarmJobs:
                collapsedJob.addExpandedJob(renderfarmJob)

            # the dependency ids are about the sub tasks holders
            # processed previously. In case there is more than
            # one await sub task holder then the dependency id
            # is going to be driven by the previous await task holder.
            for parentRenderfarmJob in parentRenderfarmJobs:
                collapsedJob.addDependencyId(parentRenderfarmJob.jobId())

            jobDataFilePath = self.__generateJobData(
                collapsedJob
            )

            # sending to the farm
            jobId = self._executeOnTheFarm(
                collapsedJob,
                jobDataFilePath
            )

            collapsedJob.setJobId(jobId)
            self.__createJobIdFile(
                jobDataFilePath,
                jobId
            )

            result.append(collapsedJob)

            # making sure the next following await task holder is going
            # to await for the current await task holder to be done
            parentRenderfarmJobs = [
                collapsedJob
            ]

        return result

    def __createJobDirectory(self):
        """
        Create a temporary job directory used to store the job configuration.
        """
        currentDate = datetime.now()
        baseRemoteTemporaryPath = os.path.join(
            self.__defaultJobTempDir,
            currentDate.strftime("%Y%m%d"),
            currentDate.strftime("%H"),
            os.environ.get("KOMBI_USER", getpass.getuser()),
            str(uuid.uuid4())
        )

        # we need to be careful when creating this path
        # since some levels of new directories may be shared with
        # different users that contain a different umask
        # (aka publishing user)
        try:
            originalUmask = os.umask(0)
            os.makedirs(baseRemoteTemporaryPath, mode=0o777)
        finally:
            os.umask(originalUmask)

        return baseRemoteTemporaryPath

    @classmethod
    def __createJobIdFile(cls, jobDataFilePath, jobId):
        """
        Create a json file based on the jobDataFilePath containing the job id.
        """
        name, ext = os.path.splitext(jobDataFilePath)
        jobIdFilePath = "{}_jobId.{ext}".format(
            name,
            ext=ext[1:]
        )

        data = {
            'id': jobId
        }

        with open(jobIdFilePath, "w") as jsonFile:
            json.dump(
                data,
                jsonFile
            )

    @classmethod
    def __chunkify(cls, inputList, chunkSize):
        """
        Return an 2D array containing the input list divided by chunks.
        """
        result = []
        if len(inputList) <= chunkSize:
            result.append(inputList)
            return result

        # adding an extra chunk for the crawlers
        # that don't fit completely in a full chunk
        totalChunks = int(len(inputList) / chunkSize)
        if len(inputList) % chunkSize:
            totalChunks += 1

        for chunk in range(totalChunks):
            currentIndex = chunk * chunkSize
            result.append(
                inputList[currentIndex:currentIndex + chunkSize]
            )

        return result
