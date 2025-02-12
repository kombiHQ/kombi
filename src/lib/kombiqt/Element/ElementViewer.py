import os
import platform
import subprocess
from kombi.Element.Fs.Image.OiioElement import OiioElement
from kombi.Element.Fs.Image import ImageElement
from kombi.Element.Fs.Video import VideoElement
from Qt import QtCore, QtGui, QtWidgets

class LoadMediaThread(QtCore.QThread):
    """
    Thread to load the file in background.
    """
    loadedSignal = QtCore.Signal(object, QtGui.QImage)
    __ffmpegExecutable = os.environ.get('KOMBI_FFMPEG_EXECUTABLE', 'ffmpeg')

    def __init__(self, element=None):
        """
        Create a LoadMediaThread object.
        """
        super(LoadMediaThread, self).__init__()
        self.setElement(element)

    def setElement(self, element, width=None, height=None):
        """
        Set the full path that should be loaded by the thread.
        """
        self.__element = element
        self.__width = width
        self.__height = height

    def run(self):
        """
        Implement the thread execution.
        """
        resultImage = QtGui.QImage()

        if isinstance(self.__element, ImageElement):
            resultImage = self.__loadImage()
        elif isinstance(self.__element, VideoElement):
            resultImage = self.__loadMovie()

        if resultImage.isNull():
            return

        if self.__width is not None and self.__height is not None:
            resultImage = resultImage.scaled(
                self.__width,
                self.__height,
                QtCore.Qt.KeepAspectRatio
            )

        self.loadedSignal.emit(self.__element, resultImage)

    def __loadMovie(self):
        """
        Load a frame from the video.
        """
        ffmpegCommand = [
            "ffmpeg",
            "-v",
            "quiet",
            "-i",
            self.__element.var('filePath'),
            "-vframes",
            "1",
            "-f",
            "image2pipe",
            "-vcodec",
            "png",
            "-"
        ]

        extraArgs = {}
        if platform.system().lower() == 'windows':
            extraArgs['creationflags'] = subprocess.CREATE_NO_WINDOW

        process = subprocess.Popen(ffmpegCommand, stdout=subprocess.PIPE, stderr=subprocess.PIPE, **extraArgs)
        stdout, _ = process.communicate()

        if process.returncode == 0:
            return QtGui.QImage.fromData(QtCore.QByteArray(stdout))

        return QtGui.QImage()

    def __loadImage(self):
        """
        Load an image.
        """
        resultImage = QtGui.QImage()
        try:
            import OpenImageIO as oiio
        except ImportError:
            resultImage = QtGui.QImage(self.__element.var('filePath'))
        else:
            # opening the source image to generate a resized image
            inputImageBuf = oiio.ImageBuf(
                OiioElement.supportedString(
                    self.__element.var('filePath')
                )
            )

            if not inputImageBuf or inputImageBuf.spec().width == 0:
                self.loadedSignal.emit(self.__element, resultImage, inputImageBuf.spec())
                return

            inputSpec = inputImageBuf.spec()
            # output spec
            outputSpec = oiio.ImageSpec(
                inputSpec.width,
                inputSpec.height,
                inputSpec.nchannels,
                inputSpec.format
            )

            # resized image buf
            resizedImageBuf = oiio.ImageBuf(
                outputSpec
            )

            temporaryBuffer = oiio.ImageBuf()
            useRGB = []
            for channelname in inputSpec.channelnames:
                if channelname.upper() in ("R", "G", "B"):
                    useRGB.append(channelname)

            oiio.ImageBufAlgo.channels(
                temporaryBuffer,
                inputImageBuf,
                ("R", "G", "B") if len(useRGB) == 3 else (inputSpec.channelnames[0],)
            )
            resizedImageBuf = temporaryBuffer

            if self.__element.var('ext').lower() in ("exr", "dpx"):
                oiio.ImageBufAlgo.colorconvert(resizedImageBuf, resizedImageBuf, "Linear", "sRGB")

            pixelData = resizedImageBuf.get_pixels(oiio.UINT8)
            resultImage = QtGui.QImage(
                pixelData,
                inputSpec.width,
                inputSpec.height,
                QtGui.QImage.Format_RGB888 if len(useRGB) else QtGui.QImage.Format_Grayscale8
            )

        return resultImage

class ElementViewer(QtWidgets.QLabel):
    """
    Basic element viewer widget.
    """

    def __init__(self, elements, showInfo=True, backgroundColor='#000000'):
        """
        Create an ElementViewer object.
        """
        super(ElementViewer, self).__init__()
        self.setMouseTracking(True)

        self.setSizePolicy(QtWidgets.QSizePolicy.Ignored, QtWidgets.QSizePolicy.Ignored)
        self.setAlignment(QtCore.Qt.AlignHCenter)

        self.__loadMediaThread = LoadMediaThread()
        self.__loadMediaThread.loadedSignal.connect(self.__finishedLoad)
        self.__setShowInfo(showInfo)

        self.__slider = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
        self.__slider.setParent(self)
        self.__slider.setTickInterval(1)
        self.__currentFileLabel = QtWidgets.QLabel()
        self.__currentFileLabel.setParent(self)

        self.__slider.valueChanged.connect(self.__onSliderChange)
        self.setStyleSheet('background-color: {}'.format(backgroundColor))

        self.setElements(elements)
        self.__reset()

    def mouseMoveEvent(self, ev):
        """
        Adjust the element sequence based on the mouse position.
        """
        self.__slider.setValue(
            QtWidgets.QStyle.sliderValueFromPosition(
                self.__slider.minimum(),
                self.__slider.maximum(),
                ev.x(),
                self.__slider.width()
            )
        )

    def resizeEvent(self, _):
        """
        Reset the current display.
        """
        self.__reset()
        self.__onSliderChange(self.__slider.value())

    def setElements(self, elements):
        """
        Set the elements that should be loaded.
        """
        self.__elements = list(sorted(elements, key=lambda x: x.var('fullPath')))
        self.__update()

    def showInfo(self):
        """
        Return if the element information widget is visible.
        """
        return self.__showInfo

    def __update(self):
        """
        Update the slider information.
        """
        if self.__elements:
            self.__slider.setMaximum(len(self.__elements) - 1)
            self.__slider.setValue(0)
            self.__onSliderChange(0)

    def __reset(self):
        """
        Invalid the current display.
        """
        self.setPixmap(QtGui.QPixmap())
        self.__currentFileLabel.setVisible(False)
        self.__slider.setVisible(False)

    def __finishedLoad(self, element, qimage):
        """
        Slot called when the thread finishes loading the image.
        """
        pixmap = QtGui.QPixmap.fromImage(qimage)
        self.setPixmap(pixmap)

        self.__slider.setFixedWidth(self.pixmap().width())
        self.__slider.move(0, self.pixmap().height() + 5)
        self.__currentFileLabel.setFixedWidth(self.pixmap().width())

        self.__currentFileLabel.setText(element.var('name'))
        self.__currentFileLabel.move(0, self.pixmap().height() + 20)

        self.__slider.setVisible(len(self.__elements) > 1)
        self.__currentFileLabel.setVisible(self.showInfo() and len(self.__elements))

    def __onSliderChange(self, value):
        """
        Slot called when the slider is changed.
        """
        if not self.__elements:
            self.__reset()
            return

        element = self.__elements[value]
        self.__loadMediaThread.setElement(element, self.width(), self.height())
        self.__loadMediaThread.start()

    def __setShowInfo(self, visible):
        """
        Specify whether the text field displaying the metadata information should be visible.
        """
        self.__showInfo = visible
