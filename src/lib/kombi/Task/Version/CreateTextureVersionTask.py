import os
from ..Task import Task
from .CreateIncrementalVersionTask import CreateIncrementalVersionTask

class CreateTextureVersionTask(CreateIncrementalVersionTask):
    """
    Create texture version task.
    """

    def __init__(self, *args, **kwargs):
        """
        Create a texture version.
        """
        super(CreateTextureVersionTask, self).__init__(*args, **kwargs)
        self.setOption('maketxArgs', '-v -u --unpremult --oiio')

    def _perform(self):
        """
        Perform the task.
        """
        for element in self.elements():

            textureOriginalTargetLocation = self.__computeTextureTargetLocation(
                element,
                element.var('ext')
            )

            # copying the original texture file
            self.copyFile(
                element.var('filePath'),
                textureOriginalTargetLocation
            )

            # executing convert texture task
            convertTexureTask = Task.create('convertTexture')
            convertTexureTask.setOption(
                'maketxArgs',
                self.option('maketxArgs')
            )

            textureTxTargetLocation = self.__computeTextureTargetLocation(element, 'tx')
            convertTexureTask.add(element, textureTxTargetLocation)
            convertTexureTask.output()

            # adding texture files to the published version
            self.addFile(textureOriginalTargetLocation)
            self.addFile(textureTxTargetLocation)

        return super(CreateTextureVersionTask, self)._perform()

    def __computeTextureTargetLocation(self, element, ext):
        """
        Compute the target file path for an texture.
        """
        return os.path.join(
            self.dataPath(),
            ext,
            "{0}_{1}.{2}".format(
                element.var('mapType'),
                element.var('udim'),
                ext
            )
        )


# registering task
Task.register(
    'createTextureVersion',
    CreateTextureVersionTask
)
