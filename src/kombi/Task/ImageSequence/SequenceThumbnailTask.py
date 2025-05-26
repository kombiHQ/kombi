from collections import OrderedDict
from ..Task import Task

class SequenceThumbnailTask(Task):
    """
    Creates a thumbnail for the image sequence.
    """

    __defaultWidth = 640
    __defaultHeight = 480

    def __init__(self, *args, **kwargs):
        """
        Create a sequence thumbnail object.
        """
        super(SequenceThumbnailTask, self).__init__(*args, **kwargs)

        self.setOption('width', self.__defaultWidth)
        self.setOption('height', self.__defaultHeight)

    def _perform(self):
        """
        Perform the task.
        """
        targetThumbnails = OrderedDict()
        for element in self.elements():
            targetFilePath = self.target(element)

            if targetFilePath not in targetThumbnails:
                targetThumbnails[targetFilePath] = []

            targetThumbnails[targetFilePath].append(element)

        result = []
        # generating a thumbnail for the sequence
        for targetThumbnail, thumbnailElements in targetThumbnails.items():
            thumbnailElement = thumbnailElements[int(len(thumbnailElements) / 2)]

            # creating a thumbnail for the image sequence
            imageThumbnailTask = Task.create('imageThumbnail')
            imageThumbnailTask.add(thumbnailElement, targetThumbnail)

            imageThumbnailTask.setOption('width', self.option('width'))
            imageThumbnailTask.setOption('height', self.option('height'))

            result += imageThumbnailTask.output()

        return result


# registering task
Task.register(
    'sequenceThumbnail',
    SequenceThumbnailTask
)
