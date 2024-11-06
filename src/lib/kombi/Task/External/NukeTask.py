import os
from .ExternalTask import ExternalTask, ExternalTaskError

class NukeTaskError(ExternalTaskError):
    """Base nuke task error."""

class NukeTask(ExternalTask):
    """
    Base nuke task.
    """

    __nukeRenderFarmGroup = os.environ.get('KOMBI_DISPATCHER_RENDERFARM_GROUP_NUKE', '')
    __nukeRenderFarmPool = os.environ.get('KOMBI_DISPATCHER_RENDERFARM_POOL_NUKE', 'nuke')
    __nukeRenderFarmSecondaryPool = os.environ.get('KOMBI_DISPATCHER_RENDERFARM_SECONDARYPOOL_NUKE', '')
    __nukeRenderFarmSplitSize = os.environ.get('KOMBI_DISPATCHER_RENDERFARM_SPLITSIZE_NUKE', '')
    __nukeRenderFarmPriority = os.environ.get('KOMBI_DISPATCHER_RENDERFARM_PRIORITY_NUKE', '')

    def __init__(self, *args, **kwargs):
        """
        Create a nuke task object.
        """
        super(NukeTask, self).__init__(*args, **kwargs)

        # required task wrapper to run nuke tasks.
        self.setMetadata('wrapper.name', 'nuke')
        self.setMetadata('wrapper.options', {})

        # default render-farm group/pools
        if self.__nukeRenderFarmGroup:
            self.setMetadata('dispatch.renderFarm.group', self.__nukeRenderFarmGroup)

        if self.__nukeRenderFarmSplitSize:
            self.setMetadata('dispatch.renderFarm.splitSize', self.__nukeRenderFarmSplitSize)

        if self.__nukeRenderFarmPool:
            self.setMetadata('dispatch.renderFarm.pool', self.__nukeRenderFarmPool)

        if self.__nukeRenderFarmSecondaryPool:
            self.setMetadata('dispatch.renderFarm.secondaryPool', self.__nukeRenderFarmSecondaryPool)

        if self.__nukeRenderFarmPriority:
            self.setMetadata('dispatch.renderFarm.priority', self.__nukeRenderFarmPriority)
