import os
from kombi.InfoCrate.Fs.Image.OiioInfoCrate import OiioInfoCrate
from Qt import QtCore, QtGui, QtWidgets
from ..Resource import Resource

class LoadImageThread(QtCore.QThread):
    loadedSignal = QtCore.Signal(str, QtGui.QImage, object)

    def __init__(self, loadImage=""):
        super(LoadImageThread, self).__init__()
        self.setImageFullPath(loadImage)

    def setImageFullPath(self, image, width=None, height=None):
        self.__loadImageFilePath = image
        self.__width = width
        self.__height = height

    def run(self):
        import OpenImageIO as oiio
        resultImage = QtGui.QImage()

        # opening the source image to generate a resized image
        inputImageBuf = oiio.ImageBuf(
            OiioInfoCrate.supportedString(
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

        if self.__width is not None and self.__height is not None:
            resultImage = resultImage.scaled(
                self.__width,
                self.__height,
                QtCore.Qt.KeepAspectRatio
            )

        self.loadedSignal.emit(self.__loadImageFilePath, resultImage, inputImageBuf.spec())


class JumpSlider(QtWidgets.QSlider):
    """
    Provides a proper jump to the position that was clicked.
    https://stackoverflow.com/questions/11132597/qslider-mouse-direct-jump/26281608
    """

    def mousePressEvent(self, ev):
        """ Jump to click position """
        self.setValue(QtWidgets.QStyle.sliderValueFromPosition(self.minimum(), self.maximum(), ev.x(), self.width()))

    def mouseMoveEvent(self, ev):
        """ Jump to pointer position while moving """
        self.setValue(QtWidgets.QStyle.sliderValueFromPosition(self.minimum(), self.maximum(), ev.x(), self.width()))

class ImageInfoCrateViewer(QtWidgets.QLabel):
    """
    Basic image infoCrate widget.
    """

    def __init__(self, imageInfoCrates, width=640, height=480):
        """
        Create an image infoCrate widget.
        """
        super(ImageInfoCrateViewer, self).__init__()

        self.setSizePolicy(QtWidgets.QSizePolicy.Ignored, QtWidgets.QSizePolicy.Ignored)
        self.setAlignment(QtCore.Qt.AlignHCenter)

        self.__loadImageThread = LoadImageThread()
        self.__loadImageThread.loadedSignal.connect(self.__finishedLoad)

        self.__slider = JumpSlider(QtCore.Qt.Orientation.Horizontal)
        self.__slider.setParent(self)
        self.__slider.setTickInterval(1)
        self.__currentFileLabel = QtWidgets.QPlainTextEdit()
        self.__currentFileLabel.setParent(self)

        self.__slider.valueChanged.connect(self.__onSliderChange)
        self.setStyleSheet("background-color: #000")

        self.setInfoCrates(imageInfoCrates)
        self.__reset()

    def resizeEvent(self, event):
        self.__reset()
        self.__onSliderChange(self.__slider.value())

    def setInfoCrates(self, imageInfoCrates):
        self.__imageInfoCrates = imageInfoCrates
        self.__update()

    def __update(self):
        if self.__imageInfoCrates:
            self.__slider.setMaximum(len(self.__imageInfoCrates) - 1)
            self.__slider.setValue(0)
            self.__onSliderChange(0)

    def __reset(self):
        self.setPixmap(
            Resource.pixmap("icons/previewPlaceHolder.png").copy().scaled(
                self.width(),
                self.height(),
                QtCore.Qt.KeepAspectRatio
            )
        )

        self.__currentFileLabel.setVisible(False)
        self.__slider.setVisible(False)

    def __finishedLoad(self, fullPath, qimage, spec):
        pixmap = QtGui.QPixmap.fromImage(qimage)
        self.setPixmap(pixmap)

        self.__slider.setFixedWidth(self.pixmap().width())
        self.__slider.move(0, self.pixmap().height() + 5)
        self.__currentFileLabel.setFixedWidth(self.pixmap().width())
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
        self.__currentFileLabel.setFixedHeight(self.height() - self.__currentFileLabel.y())

        self.__slider.setVisible(len(self.__imageInfoCrates) > 1)
        self.__currentFileLabel.setVisible(len(self.__imageInfoCrates))

    def __onSliderChange(self, value):
        if not self.__imageInfoCrates:
            self.__reset()
            return

        infoCrate = self.__imageInfoCrates[value]
        self.__loadImageThread.setImageFullPath(infoCrate.var('fullPath'), self.width(), self.height())
        self.__loadImageThread.start()
