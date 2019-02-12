from ..Task import Task
from ...Crawler import Crawler

class GafferScene(Task):
    """
    Executes a gaffer scene by triggering the task nodes.

    Required options: scene (full path of gaffer scene)

    All options defined in the task are resolved (in case the value contains a template string)
    then assigned to gaffer's context. Therefore, you can use it to
    provide custom data to gaffer.

    Since the task options are available inside of the context, it can be easily used in
    expressions, for instance the file path plug:
    /a/${myOptionName}/c

    Also, startFrame, endFrame, sourceFile and targetFile are automatically
    assigned to the context.
    """

    def __init__(self, *args, **kwargs):
        """
        Create a gaffer template task.
        """
        super(GafferScene, self).__init__(*args, **kwargs)

        self.setMetadata("wrapper.name", "gaffer")
        self.setMetadata("wrapper.options", {})
        self.setMetadata('dispatch.split', True)

    def _perform(self):
        """
        Perform the task.
        """
        import Gaffer
        import GafferDispatch

        crawlers = self.crawlers()

        # loading gaffer scene
        script = Gaffer.ScriptNode()
        script['fileName'].setValue(self.templateOption('scene', crawlers[0]))
        script.load()

        nodes = script.children(GafferDispatch.TaskNode)

        for crawlerGroup in Crawler.group(crawlers):
            for crawler in crawlerGroup:
                # adding context variables and executing task nodes
                with Gaffer.Context() as context:
                    context.set("sourceFile", crawler.var('fullPath'))
                    context.set("targetFile", self.target(crawler))

                    # adding frame range information when available
                    if 'frame' in crawler.varNames():
                        context.setFrame(crawler.var('frame'))
                        context.set("startFrame", crawlerGroup[0].var('frame'))
                        context.set("endFrame", crawlerGroup[-1].var('frame'))

                    # passing all the options to the context
                    for optionName in map(str, self.optionNames()):
                        optionValue = self.option(optionName)

                        # resolving template if necessary
                        if isinstance(optionValue, basestring):
                            optionValue = self.templateOption(optionName, crawler)

                        # adding option to the context
                        context.set(optionName, optionValue)

                    # executing task nodes
                    for node in nodes:
                        node["task"].execute()

        # default result based on the target filePath
        return super(GafferScene, self)._perform()


# registering task
Task.register(
    'gafferScene',
    GafferScene
)
