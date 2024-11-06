import os
from .ExternalTask import ExternalTask, ExternalTaskError

class HoudiniTaskError(ExternalTaskError):
    """Base houdini task error."""

class HoudiniTask(ExternalTask):
    """
    Base houdini task.
    """

    __houdiniRenderFarmGroup = os.environ.get('KOMBI_DISPATCHER_RENDERFARM_GROUP_HOUDINI', '')
    __houdiniRenderFarmPool = os.environ.get('KOMBI_DISPATCHER_RENDERFARM_POOL_HOUDINI', 'houdini')
    __houdiniRenderFarmSecondaryPool = os.environ.get('KOMBI_DISPATCHER_RENDERFARM_SECONDARYPOOL_HOUDINI', '')
    __houdiniRenderFarmSplitSize = os.environ.get('KOMBI_DISPATCHER_RENDERFARM_SPLITSIZE_HOUDINI', '')
    __houdiniRenderFarmPriority = os.environ.get('KOMBI_DISPATCHER_RENDERFARM_PRIORITY_HOUDINI', '')

    def __init__(self, *args, **kwargs):
        """
        Create a houdini task object.
        """
        super(HoudiniTask, self).__init__(*args, **kwargs)

        # required task wrapper to run houdini tasks.
        self.setMetadata('wrapper.name', 'houdini')
        self.setMetadata('wrapper.options', {})

        # default render-farm group/pools
        if self.__houdiniRenderFarmGroup:
            self.setMetadata('dispatch.renderFarm.group', self.__houdiniRenderFarmGroup)

        if self.__houdiniRenderFarmPool:
            self.setMetadata('dispatch.renderFarm.pool', self.__houdiniRenderFarmPool)

        if self.__houdiniRenderFarmSplitSize:
            self.setMetadata('dispatch.renderFarm.splitSize', self.__houdiniRenderFarmSplitSize)

        if self.__houdiniRenderFarmSecondaryPool:
            self.setMetadata('dispatch.renderFarm.secondaryPool', self.__houdiniRenderFarmSecondaryPool)

        if self.__houdiniRenderFarmPriority:
            self.setMetadata('dispatch.renderFarm.priority', self.__houdiniRenderFarmPriority)
