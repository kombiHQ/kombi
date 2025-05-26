import os
from .ExternalTask import ExternalTask, ExternalTaskError

class MayaTaskError(ExternalTaskError):
    """Base maya task error."""

class MayaTask(ExternalTask):
    """
    Base maya task.
    """

    __mayaRenderFarmGroup = os.environ.get('KOMBI_DISPATCHER_RENDERFARM_GROUP_MAYA', '')
    __mayaRenderFarmPool = os.environ.get('KOMBI_DISPATCHER_RENDERFARM_POOL_MAYA', 'maya')
    __mayaRenderFarmSecondaryPool = os.environ.get('KOMBI_DISPATCHER_RENDERFARM_SECONDARYPOOL_MAYA', '')
    __mayaRenderFarmSplitSize = os.environ.get('KOMBI_DISPATCHER_RENDERFARM_SPLITSIZE_MAYA', '')
    __mayaRenderFarmPriority = os.environ.get('KOMBI_DISPATCHER_RENDERFARM_PRIORITY_MAYA', '')

    def __init__(self, *args, **kwargs):
        """
        Create a maya task object.
        """
        super(MayaTask, self).__init__(*args, **kwargs)

        # required task wrapper to run maya tasks.
        self.setMetadata('wrapper.name', 'maya')
        self.setMetadata('wrapper.options', {})

        # default render-farm group/pools
        if self.__mayaRenderFarmGroup:
            self.setMetadata('dispatch.renderFarm.group', self.__mayaRenderFarmGroup)

        if self.__mayaRenderFarmPool:
            self.setMetadata('dispatch.renderFarm.pool', self.__mayaRenderFarmPool)

        if self.__mayaRenderFarmSplitSize:
            self.setMetadata('dispatch.renderFarm.splitSize', self.__mayaRenderFarmSplitSize)

        if self.__mayaRenderFarmSecondaryPool:
            self.setMetadata('dispatch.renderFarm.secondaryPool', self.__mayaRenderFarmSecondaryPool)

        if self.__mayaRenderFarmPriority:
            self.setMetadata('dispatch.renderFarm.priority', self.__mayaRenderFarmPriority)
