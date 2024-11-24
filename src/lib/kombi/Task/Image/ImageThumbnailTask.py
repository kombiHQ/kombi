from ..Task import Task

class ImageThumbnailTask(Task):
    """
    Generates a thumbnail for the input image keeping the aspect ratio.

    Options:
        - Optional: "convertToRGBA"
    """

    __defaultWidth = 640
    __defaultHeight = 480
    __defaultConvertToRGBA = True

    def __init__(self, *args, **kwargs):
        """
        Create a image thumbnail object.
        """
        super(ImageThumbnailTask, self).__init__(*args, **kwargs)

        self.setOption('width', self.__defaultWidth)
        self.setOption('height', self.__defaultHeight)
        self.setOption("convertToRGBA", self.__defaultConvertToRGBA)
        self.setMetadata('dispatch.split', True)

    def _perform(self):
        """
        Perform the task.
        """
        width = self.option('width')
        height = self.option('height')

        result = []
        for infoCrate in self.infoCrates():
            targetFilePath = self.target(infoCrate)

            # creating a task to resize the thumbnail
            resizeImageTask = Task.create('resizeImage')
            resizeImageTask.setOption('convertToRGBA', self.option('convertToRGBA'))
            resizeImageTask.add(infoCrate, targetFilePath)

            # Calculate resize ratios for resizing
            currentWidth = infoCrate.var('width')
            currentHeigth = infoCrate.var('height')

            ratioWidth = width / float(currentWidth)
            ratioHeight = height / float(currentHeigth)

            # smaller ratio will ensure that the image fits in the view
            ratio = ratioWidth if ratioWidth < ratioHeight else ratioHeight

            newWidth = int(currentWidth * ratio)
            newHeight = int(currentHeigth * ratio)

            resizeImageTask.setOption(
                'width',
                newWidth
            )

            resizeImageTask.setOption(
                'height',
                newHeight
            )

            # running task
            result += resizeImageTask.output()

        return result


# registering task
Task.register(
    'imageThumbnail',
    ImageThumbnailTask
)
