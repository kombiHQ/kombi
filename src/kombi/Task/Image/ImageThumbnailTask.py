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

    def _processElement(self, element):
        """
        Process an individual element.
        """
        width = self.option('width', element)
        if isinstance(width, str):
            width = int(width)

        height = self.option('height', element)
        if isinstance(height, str):
            height = int(height)

        targetFilePath = self.target(element)

        # creating a task to resize the thumbnail
        resizeImageTask = Task.create('resizeImage')
        resizeImageTask.setOption('convertToRGBA', self.option('convertToRGBA'))
        resizeImageTask.add(element, targetFilePath)

        # Calculate resize ratios for resizing
        currentWidth = element.var('width')
        currentHeigth = element.var('height')

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
        return resizeImageTask.output()[0]


# registering task
Task.register(
    'imageThumbnail',
    ImageThumbnailTask
)
