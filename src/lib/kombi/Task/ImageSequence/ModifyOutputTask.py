from ..Task import Task

class ModifyOutputTask(Task):
    """
    Task used to modify the output by assign infoCrate vars and tags.
    """

    def __init__(self, *args, **kwargs):
        """
        Create a modify infoCrates task object.
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

        for infoCrate in self.infoCrates():
            newInfoCrate = infoCrate.clone()

            # vars
            for varName, varValue in self.templateOption('assignVars', infoCrate).items():
                newInfoCrate.setVar(varName, varValue)

            # context vars
            for varName, varValue in self.templateOption('assignContextVars', infoCrate).items():
                newInfoCrate.setVar(varName, varValue, True)

            # tags
            for tagName, tagValue in self.templateOption('assignTags', infoCrate).items():
                newInfoCrate.setTar(tagName, tagValue)

            result.append(newInfoCrate)

        return result


Task.register('modifyOutput', ModifyOutputTask)
