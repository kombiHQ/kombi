from ..Task import Task

class ModifyOutputTask(Task):
    """
    Task used to modify the output by assign crawler vars and tags.
    """

    def __init__(self, *args, **kwargs):
        """
        Create a modify crawlers task object.
        """
        super(ModifyOutputTask, self).__init__(*args, **kwargs)

        self.setOption('assignVars', {})
        self.setOption('assignContextVars', {})
        self.setOption('assignTags', {})

    def _perform(self):
        """
        Perform the task.
        """
        result = []

        for crawler in self.crawlers():
            newCrawler = crawler.clone()

            # vars
            for varName, varValue in self.templateOption('assignVars', crawler).items():
                newCrawler.setVar(varName, varValue)

            # context vars
            for varName, varValue in self.templateOption('assignContextVars', crawler).items():
                newCrawler.setVar(varName, varValue, True)

            # tags
            for tagName, tagValue in self.templateOption('assignTags', crawler).items():
                newCrawler.setTar(tagName, tagValue)

            result.append(newCrawler)

        return result


Task.register('modifyOutput', ModifyOutputTask)
