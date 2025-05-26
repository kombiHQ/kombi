from ..Task import Task

class ModifyOutputTask(Task):
    """
    Task used to modify the output by assign element vars and tags.
    """

    def __init__(self, *args, **kwargs):
        """
        Create a modify elements task object.
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

        for element in self.elements():
            newElement = element.clone()

            # vars
            for varName, varValue in self.option('assignVars', element).items():
                newElement.setVar(varName, varValue)

            # context vars
            for varName, varValue in self.option('assignContextVars', element).items():
                newElement.setVar(varName, varValue, True)

            # tags
            for tagName, tagValue in self.option('assignTags', element).items():
                newElement.setTar(tagName, tagValue)

            result.append(newElement)

        return result


Task.register('modifyOutput', ModifyOutputTask)
