import os
from kombi.Element.Fs.Image.OiioElement import OiioElement
from Qt import QtCore, QtGui, QtWidgets

class LoadImageThread(QtCore.QThread):
    """
    Thread to load the image in background.
    """
    loadedSignal = QtCore.Signal(str, QtGui.QImage, object)

    def __init__(self, loadImage=""):
        """
        Create a LoadImageThread object.
        """
        super(LoadImageThread, self).__init__()
        self.setImageFullPath(loadImage)

    def setImageFullPath(self, image, width=None, height=None):
        """
        Set the image full path that should be loaded by the thread.
        """
        self.__loadImageFilePath = image
        self.__width = width
        self.__height = height

    def run(self):
        """
        Implement the thread execution.
        """
        resultImage = QtGui.QImage()
        spec = None

        try:
            import OpenImageIO as oiio
        except ImportError:
            resultImage = QtGui.QImage(self.__loadImageFilePath)
        else:
            # opening the source image to generate a resized image
            inputImageBuf = oiio.ImageBuf(
                OiioElement.supportedString(
                    self.__loadImageFilePath
                )
            )

            if not inputImageBuf or inputImageBuf.spec().width == 0:
                self.loadedSignal.emit(self.__loadImageFilePath, resultImage, inputImageBuf.spec())
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

            if os.path.splitext(self.__loadImageFilePath)[-1].lower() in (".exr", ".dpx"):
                oiio.ImageBufAlgo.colorconvert(resizedImageBuf, resizedImageBuf, "Linear", "sRGB")

            pixelData = resizedImageBuf.get_pixels(oiio.UINT8)
            resultImage = QtGui.QImage(
                pixelData,
                inputSpec.width,
                inputSpec.height,
                QtGui.QImage.Format_RGB888 if len(useRGB) else QtGui.QImage.Format_Grayscale8
            )
            spec = inputImageBuf.spec()

        if resultImage.isNull():
            return

        if self.__width is not None and self.__height is not None:
            resultImage = resultImage.scaled(
                self.__width,
                self.__height,
                QtCore.Qt.KeepAspectRatio
            )

        self.loadedSignal.emit(self.__loadImageFilePath, resultImage, spec)

class ElementViewer(QtWidgets.QLabel):
    """
    Basic image element widget.
    """

    def __init__(self, imageElements, showInfo=True, backgroundColor='#000000'):
        """
        Create an image element widget.
        """
        super(ElementViewer, self).__init__()
        self.setMouseTracking(True)

        self.setSizePolicy(QtWidgets.QSizePolicy.Ignored, QtWidgets.QSizePolicy.Ignored)
        self.setAlignment(QtCore.Qt.AlignHCenter)

        self.__loadImageThread = LoadImageThread()
        self.__loadImageThread.loadedSignal.connect(self.__finishedLoad)
        self.__setShowInfo(showInfo)

        self.__slider = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
        self.__slider.setParent(self)
        self.__slider.setTickInterval(1)
        self.__currentFileLabel = QtWidgets.QPlainTextEdit()
        self.__currentFileLabel.setParent(self)

        self.__slider.valueChanged.connect(self.__onSliderChange)
        self.setStyleSheet("background-color: {}".format(backgroundColor))

        self.setElements(imageElements)
        self.__reset()

    def mouseMoveEvent(self, ev):
        """
        Adjust the image sequence based on the mouse position.
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

    def setElements(self, imageElements):
        """
        Set the elements that should be loaded.
        """
        self.__imageElements = list(sorted(imageElements, key=lambda x: x.var('fullPath')))
        self.__update()

    def showInfo(self):
        """
        Return if the image information widget is visible.
        """
        return self.__showInfo

    def __update(self):
        """
        Update the slider information.
        """
        if self.__imageElements:
            self.__slider.setMaximum(len(self.__imageElements) - 1)
            self.__slider.setValue(0)
            self.__onSliderChange(0)

    def __reset(self):
        """
        Invalid the current display.
        """
        self.setPixmap(QtGui.QPixmap())
        self.__currentFileLabel.setVisible(False)
        self.__slider.setVisible(False)

    def __finishedLoad(self, fullPath, qimage, spec):
        """
        Slot called when the thread finishes loading the image.
        """
        pixmap = QtGui.QPixmap.fromImage(qimage)
        self.setPixmap(pixmap)

        self.__slider.setFixedWidth(self.pixmap().width())
        self.__slider.move(0, self.pixmap().height() + 5)
        self.__currentFileLabel.setFixedWidth(self.pixmap().width())

        if spec is not None:
            textLines = [os.path.basename(fullPath)]
            textLines.append("")
            textLines.append("Spec:")
            textLines.append("  Resolution: {} x {}".format(spec.width, spec.height))
            textLines.append("  Format: {}".format(spec.format))
            textLines.append("  Channels: {}".format(", ".join(spec.channelnames)))

            metadata = []
            for param in spec.extra_attribs:
                metadata.append("  {}: {}".format(param.name, str(param.value)))

            if metadata:
                textLines.append("")
                textLines.append("Metadata:")
                textLines += metadata

            self.__currentFileLabel.setPlainText('\n'.join(textLines))
        self.__currentFileLabel.setReadOnly(True)
        self.__currentFileLabel.move(0, self.pixmap().height() + 20)
        currentFileHeight = self.height() - self.__currentFileLabel.y()
        if currentFileHeight > 0:
            self.__currentFileLabel.setFixedHeight(currentFileHeight)

        self.__slider.setVisible(len(self.__imageElements) > 1)
        self.__currentFileLabel.setVisible(self.showInfo() and len(self.__imageElements))

    def __onSliderChange(self, value):
        """
        Slot called when the slider is changed.
        """
        if not self.__imageElements:
            self.__reset()
            return

        element = self.__imageElements[value]
        self.__loadImageThread.setImageFullPath(element.var('fullPath'), self.width(), self.height())
        self.__loadImageThread.start()

    def __setShowInfo(self, visible):
        """
        Specify whether the text field displaying the image information should be visible
        """
        self.__showInfo = visible
