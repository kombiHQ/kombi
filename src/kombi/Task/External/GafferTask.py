import os
from .ExternalTask import ExternalTask, ExternalTaskError

class GafferTaskError(ExternalTaskError):
    """Base gaffer task error."""

class GafferTask(ExternalTask):
    """
    Base gaffer task.
    """

    __gafferRenderFarmGroup = os.environ.get('KOMBI_DISPATCHER_RENDERFARM_GROUP_GAFFER', '')
    __gafferRenderFarmPool = os.environ.get('KOMBI_DISPATCHER_RENDERFARM_POOL_GAFFER', 'gaffer')
    __gafferRenderFarmSecondaryPool = os.environ.get('KOMBI_DISPATCHER_RENDERFARM_SECONDARYPOOL_GAFFER', '')
    __gafferRenderFarmSplitSize = os.environ.get('KOMBI_DISPATCHER_RENDERFARM_SPLITSIZE_GAFFER', '')
    __gafferRenderFarmPriority = os.environ.get('KOMBI_DISPATCHER_RENDERFARM_PRIORITY_GAFFER', '')

    def __init__(self, *args, **kwargs):
        """
        Create a gaffer task object.
        """
        super(GafferTask, self).__init__(*args, **kwargs)

        # required task wrapper to run gaffer tasks.
        self.setMetadata('wrapper.name', 'gaffer')
        self.setMetadata('wrapper.options', {})

        # default render-farm group/pools
        if self.__gafferRenderFarmGroup:
            self.setMetadata('dispatch.renderFarm.group', self.__gafferRenderFarmGroup)

        if self.__gafferRenderFarmPool:
            self.setMetadata('dispatch.renderFarm.pool', self.__gafferRenderFarmPool)

        if self.__gafferRenderFarmSecondaryPool:
            self.setMetadata('dispatch.renderFarm.secondaryPool', self.__gafferRenderFarmSecondaryPool)

        if self.__gafferRenderFarmSplitSize:
            self.setMetadata('dispatch.renderFarm.splitSize', self.__gafferRenderFarmSplitSize)

        if self.__gafferRenderFarmPriority:
            self.setMetadata('dispatch.renderFarm.priority', self.__gafferRenderFarmPriority)

    @classmethod
    def collectAncestors(cls, node, nodeType):
        """
        Return a list of ancestors for the input node type.
        """
        import Gaffer

        if 'in' not in node:
            return []

        result = []
        for childPlug in node['in'].children() or [] if isinstance(node['in'], Gaffer.ArrayPlug) else [node['in']]:
            if childPlug.getInput():
                if isinstance(childPlug.getInput().node(), nodeType):
                    result.append(childPlug.getInput().node())
                result += cls.collectAncestors(childPlug.getInput().node(), nodeType)

        return result
