from .Subprocess import Subprocess

# checking for immupipe support
try:
    import basetools
except ImportError:
    basetoolsAvailable = False
else:
    basetoolsAvailable = True

class DCC(Subprocess):
    """
    ABC to perform a task inside of a DCC (like maya, nuke...).
    """

    def _perform(self, task):
        """
        Implement the execution of the subprocess wrapper.
        """
        taskScenePath = ''
        if 'scenePath' in task.optionNames():
            taskScenePath = task.option('scenePath')

        # we want to double check if we are already inside of the target DCC if so, lets use the current DCC session
        # in case the scenePath defined as option of the task matches the current scene scene in the DCC. In case
        # the DCC does not have any scene opened we load the scene from the task.
        insideDCC = False
        if basetoolsAvailable:
            try:
                appHook = basetools.App.to(self._hookName())
                appContext = appHook.context()
            except basetools.App.HookNotRegisteredError:
                pass
            else:
                # loading the scene
                if appContext.isEmpty():
                    # \TODO: we need an abstracted way that we can tell context to load a scene file.
                    if taskScenePath:
                        # appContext.openFile(taskScenePath)
                        pass

                    insideDCC = True

                elif taskScenePath == appContext.fileName():
                    insideDCC = True

        # we need to launch DCC first
        if not insideDCC:
            return super(DCC, self)._perform(task)

        # otherwise we can execute the task right away
        else:
            return task.output()

    def _command(self):
        """
        For re-implementation: should return a string which is executed as subprocess.
        """
        raise NotImplementedError

    @classmethod
    def _hookName(cls):
        """
        For re-implementation: should return a string containing the name used for the hook registered in basetools.
        """
        raise NotImplementedError
